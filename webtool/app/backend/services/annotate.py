from __future__ import annotations

from typing import List, Dict, Any
from .cosmic_client import get_cosmic_client


def annotate_with_databases(variants: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
	"""Annotate variants with COSMIC database information"""
	cosmic_client = get_cosmic_client()
	annotations: Dict[str, Dict[str, Any]] = {}
	
	for idx, v in enumerate(variants):
		key = _vk(v, idx)
		gene = v.get("gene", "")
		chrom = v.get("chrom", "")
		pos = v.get("pos")
		ref = v.get("ref", "")
		alt = v.get("alt", "")
		
		# Search COSMIC for this variant
		cosmic_data = {}
		if gene and chrom and pos and ref and alt:
			try:
				# Try coordinate-based search first
				cosmic_result = cosmic_client.search_by_coordinates(chrom, pos, ref, alt)
				if cosmic_result.get("results"):
					mutation = cosmic_result["results"][0]
					cosmic_data = {
						"match": True,
						"id": mutation.get("cosmic_id"),
						"frequency": mutation.get("frequency", 0),
						"cancer_types": mutation.get("cancer_types", []),
						"pathogenicity": mutation.get("pathogenicity", "Unknown"),
						"clinical_significance": mutation.get("clinical_significance", "Unknown")
					}
				else:
					# Try gene-based search
					gene_result = cosmic_client.search_mutations(gene, limit=10)
					if gene_result.get("results"):
						cosmic_data = {
							"match": True,
							"id": f"GENE_{gene}",
							"frequency": 0,
							"cancer_types": gene_result["results"][0].get("cancer_types", []),
							"pathogenicity": "Unknown",
							"clinical_significance": "Unknown"
						}
			except Exception:
				cosmic_data = {"match": False, "id": None, "error": "Search failed"}
		
		annotations[key] = {
			"COSMIC": cosmic_data,
			"ClinVar": {"clinical_significance": cosmic_data.get("clinical_significance", "unknown")},
			"MyCancerGenome": {"evidence": cosmic_data.get("pathogenicity", None)},
			"links": [],
		}
	
	return annotations


def clinical_actionability(annotations: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
	"""Determine clinical actionability based on annotations"""
	output: Dict[str, Any] = {}
	
	for key, ann in annotations.items():
		flag = False
		therapy = []
		
		cosmic_data = ann.get("COSMIC", {})
		if cosmic_data.get("match"):
			flag = True
			# Add therapy suggestions based on COSMIC data
			cancer_types = cosmic_data.get("cancer_types", [])
			pathogenicity = cosmic_data.get("pathogenicity", "")
			
			if "Breast" in cancer_types:
				therapy.append({"drug": "Olaparib", "status": "FDA-approved", "indication": "BRCA-mutated breast cancer"})
			if "Colon" in cancer_types:
				therapy.append({"drug": "Cetuximab", "status": "FDA-approved", "indication": "Colorectal cancer"})
			if "Lung" in cancer_types:
				therapy.append({"drug": "Gefitinib", "status": "FDA-approved", "indication": "EGFR-mutated lung cancer"})
			
			if not therapy:  # Generic therapy if no specific match
				therapy.append({"drug": "Standard chemotherapy", "status": "Available", "indication": "General cancer treatment"})
		
		output[key] = {
			"actionable": flag, 
			"therapies": therapy,
			"confidence": "high" if cosmic_data.get("frequency", 0) > 0.1 else "medium"
		}
	
	return output


def _vk(v: Dict[str, Any], idx: int) -> str:
	"""Generate variant key"""
	return f"{v.get('gene','GENE')}:{v.get('protein_change','p.?')}#{idx}"
