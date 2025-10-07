from typing import List, Dict, Any
import random

ALGORITHMS = ["SIFT", "PolyPhen-2", "PROVEAN", "MutationAssessor"]
ENSEMBLE = ["REVEL", "MetaLR"]


def run_scoring_algorithms(
	variants: List[Dict[str, Any]], analyses: List[str], options: Dict[str, Any]
) -> Dict[str, Dict[str, float]]:
	scores: Dict[str, Dict[str, float]] = {}
	for idx, variant in enumerate(variants):
		key = _variant_key(variant, idx)
		scores[key] = {}
		for algo in ALGORITHMS:
			if algo in analyses or "all" in analyses:
				rnd = _stable_random_number(str(variant) + algo)
				scores[key][algo] = rnd
	return scores


def run_ensemble_scores(scores: Dict[str, Dict[str, float]]) -> Dict[str, Dict[str, float]]:
	ensemble_scores: Dict[str, Dict[str, float]] = {}
	for key, s in scores.items():
		if not s:
			continue
		avg = sum(s.values()) / max(len(s), 1)
		ensemble_scores[key] = {
			"REVEL": min(max(avg * 0.9 + 0.05, 0.0), 1.0),
			"MetaLR": min(max(avg * 0.8 + 0.1, 0.0), 1.0),
		}
	return ensemble_scores


def _variant_key(variant: Dict[str, Any], idx: int) -> str:
	chrom = variant.get("chrom", "chr?")
	pos = variant.get("pos", "?")
	ref = variant.get("ref", "?")
	alt = variant.get("alt", "?")
	return f"{chrom}:{pos}{ref}>{alt}#{idx}"


def _stable_random_number(seed: str) -> float:
	random.seed(seed)
	return round(random.random(), 4)
