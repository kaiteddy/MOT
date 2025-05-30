"""
Ensemble pipeline that combines multiple Vision-Language Models for maximum accuracy.
"""
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from statistics import mean, median
import re

from ..vision_models.base_vision_model import BaseVisionModel, ExtractionResult, ModelConfig
from ..vision_models.claude_vision import ClaudeVisionModel
from ..vision_models.gpt4_vision import GPT4VisionModel
from ..vision_models.gemini_vision import GeminiVisionModel
from ..vision_models.florence_vision import FlorenceVisionModel
from ..validation.uk_registration_validator import UKRegistrationValidator
from ..validation.date_validator import DateValidator
from config.settings import settings


@dataclass
class EnsembleResult:
    """Result from ensemble processing."""
    final_extraction: ExtractionResult
    individual_results: List[ExtractionResult]
    consensus_scores: Dict[str, float]
    agreement_level: float
    processing_time: float
    models_used: List[str]
    validation_results: Dict[str, bool]
    requires_manual_review: bool


class EnsemblePipeline:
    """Ensemble pipeline combining multiple vision models for maximum accuracy."""

    def __init__(self):
        self.models: List[BaseVisionModel] = []
        self.model_weights = settings.model_weights
        self.registration_validator = UKRegistrationValidator()
        self.date_validator = DateValidator()
        self._initialize_models()

    def _initialize_models(self):
        """Initialize all available vision models."""
        try:
            # Initialize Claude 3.5 Sonnet
            if settings.anthropic_api_key:
                claude_config = ModelConfig(
                    api_key=settings.anthropic_api_key,
                    model_name=settings.claude_model,
                    max_tokens=settings.claude_max_tokens,
                    temperature=settings.claude_temperature
                )
                self.models.append(ClaudeVisionModel(claude_config))

            # Initialize GPT-4 Vision
            if settings.openai_api_key:
                gpt4v_config = ModelConfig(
                    api_key=settings.openai_api_key,
                    model_name=settings.openai_model,
                    max_tokens=settings.openai_max_tokens,
                    temperature=settings.openai_temperature
                )
                self.models.append(GPT4VisionModel(gpt4v_config))

            # Initialize Gemini Pro Vision
            if settings.google_api_key:
                gemini_config = ModelConfig(
                    api_key=settings.google_api_key,
                    model_name=settings.gemini_model,
                    temperature=settings.gemini_temperature
                )
                self.models.append(GeminiVisionModel(gemini_config))

            # Initialize Florence-2 (local model, no API key required)
            try:
                florence_config = ModelConfig(
                    api_key="",  # Not needed for local model
                    model_name=settings.florence_model
                )
                self.models.append(FlorenceVisionModel(florence_config))
            except Exception as e:
                # Florence-2 is optional, continue without it if it fails
                print(f"Warning: Could not initialize Florence-2: {str(e)}")

        except Exception as e:
            raise RuntimeError(f"Failed to initialize vision models: {str(e)}")

    async def process_screenshot(self, image_path: str) -> EnsembleResult:
        """
        Process screenshot using ensemble of vision models.

        Args:
            image_path: Path to the screenshot image

        Returns:
            EnsembleResult with consensus extraction and metadata
        """
        start_time = time.time()

        # Run all models concurrently
        individual_results = await self._run_all_models(image_path)

        # Calculate consensus
        consensus_extraction = self._calculate_consensus(individual_results)

        # Validate results
        validation_results = self._validate_consensus(consensus_extraction)

        # Calculate agreement level
        agreement_level = self._calculate_agreement_level(individual_results)

        # Determine if manual review is needed
        requires_manual_review = self._requires_manual_review(
            consensus_extraction, validation_results, agreement_level
        )

        processing_time = time.time() - start_time

        return EnsembleResult(
            final_extraction=consensus_extraction,
            individual_results=individual_results,
            consensus_scores=self._calculate_consensus_scores(individual_results),
            agreement_level=agreement_level,
            processing_time=processing_time,
            models_used=[result.model_name for result in individual_results],
            validation_results=validation_results,
            requires_manual_review=requires_manual_review
        )

    async def _run_all_models(self, image_path: str) -> List[ExtractionResult]:
        """
        Run all available models concurrently.

        Args:
            image_path: Path to the image

        Returns:
            List of extraction results from all models
        """
        tasks = []
        for model in self.models:
            task = asyncio.create_task(model.extract_mot_data(image_path))
            tasks.append(task)

        # Wait for all models to complete (with timeout)
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=settings.model_timeout
            )

            # Filter out exceptions and return successful results
            successful_results = []
            for result in results:
                if isinstance(result, ExtractionResult):
                    successful_results.append(result)
                else:
                    # Log the exception but continue with other models
                    print(f"Model failed: {str(result)}")

            return successful_results

        except asyncio.TimeoutError:
            raise RuntimeError("Model processing timeout exceeded")

    def _calculate_consensus(self, results: List[ExtractionResult]) -> ExtractionResult:
        """
        Calculate consensus extraction from multiple model results.

        Args:
            results: List of extraction results from different models

        Returns:
            Consensus ExtractionResult
        """
        if not results:
            raise ValueError("No successful model results to process")

        # For each field, calculate weighted consensus
        consensus_data = {}
        consensus_confidence = {}

        fields = ['registration', 'mot_expiry', 'make', 'model',
                 'customer_name', 'customer_phone', 'customer_email']

        for field in fields:
            field_values = []
            field_confidences = []
            field_weights = []

            for result in results:
                value = getattr(result, field)
                confidence = result.confidence_scores.get(field, 0.0)
                model_weight = self.model_weights.get(result.model_name, 0.1)

                if value != "NOT_FOUND" and confidence > 0.3:
                    field_values.append(value)
                    field_confidences.append(confidence)
                    field_weights.append(model_weight)

            # Calculate consensus value and confidence
            if field_values:
                consensus_value, consensus_conf = self._weighted_consensus(
                    field_values, field_confidences, field_weights
                )
                consensus_data[field] = consensus_value
                consensus_confidence[field] = consensus_conf
            else:
                consensus_data[field] = "NOT_FOUND"
                consensus_confidence[field] = 0.0

        # Create consensus result
        return ExtractionResult(
            registration=consensus_data['registration'],
            mot_expiry=consensus_data['mot_expiry'],
            make=consensus_data['make'],
            model=consensus_data['model'],
            customer_name=consensus_data['customer_name'],
            customer_phone=consensus_data['customer_phone'],
            customer_email=consensus_data['customer_email'],
            confidence_scores=consensus_confidence,
            software_detected=self._consensus_software(results),
            raw_response="ENSEMBLE_CONSENSUS",
            processing_time=sum(r.processing_time for r in results),
            model_name="ENSEMBLE"
        )

    def _weighted_consensus(
        self,
        values: List[str],
        confidences: List[float],
        weights: List[float]
    ) -> tuple[str, float]:
        """
        Calculate weighted consensus for a field.

        Args:
            values: List of extracted values
            confidences: List of confidence scores
            weights: List of model weights

        Returns:
            Tuple of (consensus_value, consensus_confidence)
        """
        if not values:
            return "NOT_FOUND", 0.0

        # Group identical values
        value_groups = {}
        for i, value in enumerate(values):
            normalized_value = self._normalize_value(value)
            if normalized_value not in value_groups:
                value_groups[normalized_value] = {
                    'original_values': [],
                    'confidences': [],
                    'weights': []
                }
            value_groups[normalized_value]['original_values'].append(value)
            value_groups[normalized_value]['confidences'].append(confidences[i])
            value_groups[normalized_value]['weights'].append(weights[i])

        # Calculate weighted scores for each group
        best_score = 0.0
        best_value = "NOT_FOUND"

        for normalized_value, group in value_groups.items():
            # Calculate weighted score
            total_weight = sum(group['weights'])
            weighted_confidence = sum(
                conf * weight for conf, weight in zip(group['confidences'], group['weights'])
            ) / total_weight if total_weight > 0 else 0.0

            # Bonus for multiple model agreement
            agreement_bonus = min(len(group['original_values']) * 0.1, 0.3)
            final_score = weighted_confidence + agreement_bonus

            if final_score > best_score:
                best_score = final_score
                # Choose the most common original value in this group
                best_value = max(set(group['original_values']),
                               key=group['original_values'].count)

        return best_value, min(best_score, 1.0)

    def _normalize_value(self, value: str) -> str:
        """Normalize value for comparison (remove spaces, case, etc.)."""
        if not value or value == "NOT_FOUND":
            return value
        return re.sub(r'\s+', '', value.upper())

    def _consensus_software(self, results: List[ExtractionResult]) -> str:
        """Determine consensus software detection."""
        software_detections = [r.software_detected for r in results if r.software_detected != "UNKNOWN"]
        if software_detections:
            return max(set(software_detections), key=software_detections.count)
        return "UNKNOWN"

    def _calculate_consensus_scores(self, results: List[ExtractionResult]) -> Dict[str, float]:
        """Calculate consensus confidence scores."""
        if not results:
            return {}

        fields = ['registration', 'mot_expiry', 'make', 'model',
                 'customer_name', 'customer_phone', 'customer_email']

        consensus_scores = {}
        for field in fields:
            scores = [r.confidence_scores.get(field, 0.0) for r in results]
            consensus_scores[field] = mean(scores) if scores else 0.0

        return consensus_scores
