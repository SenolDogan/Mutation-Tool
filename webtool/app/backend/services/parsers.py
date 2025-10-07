from typing import List, Dict, Any
import io
import csv
import json
import pandas as pd

try:
	from cyvcf2 import VCF  # type: ignore
except Exception:  # noqa: BLE001
	VCF = None


def parse_variant_file(filename: str, content: bytes) -> List[Dict[str, Any]]:
	lower = filename.lower()
	if lower.endswith(".vcf") or lower.endswith(".vcf.gz"):
		if VCF is None:
			raise RuntimeError("VCF parsing is disabled (cyvcf2 not installed). Please upload CSV/JSON.")
		return _parse_vcf(content)
	if lower.endswith(".csv"):
		return _parse_csv(content)
	if lower.endswith(".json"):
		return _parse_json(content)
	if lower.endswith(".xlsx"):
		return _parse_excel(content)
	raise ValueError("Unsupported file type. Use VCF, CSV, JSON, or Excel.")


def _parse_vcf(content: bytes) -> List[Dict[str, Any]]:
	# Placeholder; not supported without filesystem temp path
	raise RuntimeError("VCF parsing not available in this build. Use CSV/JSON.")


def _parse_csv(content: bytes) -> List[Dict[str, Any]]:
	text = content.decode("utf-8", errors="ignore")
	reader = csv.DictReader(io.StringIO(text))
	variants: List[Dict[str, Any]] = []
	for row in reader:
		variant = {
			"chrom": row.get("chrom"),
			"pos": _to_int(row.get("pos")),
			"ref": row.get("ref"),
			"alt": row.get("alt"),
			"gene": row.get("gene"),
			"protein_change": row.get("protein_change"),
		}
		variants.append(variant)
	return variants


def _parse_json(content: bytes) -> List[Dict[str, Any]]:
	data = json.loads(content.decode("utf-8", errors="ignore"))
	if isinstance(data, dict) and "variants" in data:
		data = data["variants"]
	if not isinstance(data, list):
		raise ValueError("JSON must be a list of variant records or have a 'variants' list")
	return data


def _parse_excel(content: bytes) -> List[Dict[str, Any]]:
	"""Parse Excel file (.xlsx) containing variant data"""
	try:
		# Read Excel file from bytes
		excel_file = io.BytesIO(content)
		df = pd.read_excel(excel_file, engine='openpyxl')
		
		# Convert DataFrame to list of dictionaries
		variants = []
		for _, row in df.iterrows():
			variant = {
				"chrom": str(row.get("chrom", "")),
				"pos": _to_int(row.get("pos")),
				"ref": str(row.get("ref", "")),
				"alt": str(row.get("alt", "")),
				"gene": str(row.get("gene", "")),
				"protein_change": str(row.get("protein_change", "")),
			}
			variants.append(variant)
		return variants
	except Exception as e:
		raise ValueError(f"Error parsing Excel file: {str(e)}")


def _to_int(value):
	try:
		return int(value) if value is not None else None
	except Exception:  # noqa: BLE001
		return None
