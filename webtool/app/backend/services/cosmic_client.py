from __future__ import annotations

import requests
import time
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)


class COSMICClient:
    """Client for COSMIC (Catalogue of Somatic Mutations in Cancer) API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://cancer.sanger.ac.uk/cosmic/api/v1"
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({"Authorization": f"Bearer {api_key}"})
        self.session.headers.update({
            "User-Agent": "Cancer-Mutation-Analysis-Tool/1.0",
            "Accept": "application/json"
        })
    
    def search_mutations(self, gene: str, mutation: str = "", limit: int = 100) -> Dict[str, Any]:
        """Search for mutations in COSMIC database"""
        try:
            params = {
                "gene": gene.upper(),
                "limit": limit
            }
            if mutation:
                params["mutation"] = mutation
            
            response = self.session.get(
                f"{self.base_url}/mutations",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"COSMIC API error: {e}")
            return {"error": str(e), "results": []}
    
    def get_gene_info(self, gene: str) -> Dict[str, Any]:
        """Get gene information from COSMIC"""
        try:
            response = self.session.get(
                f"{self.base_url}/genes/{gene.upper()}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"COSMIC gene API error: {e}")
            return {"error": str(e)}
    
    def search_by_coordinates(self, chromosome: str, position: int, ref: str, alt: str) -> Dict[str, Any]:
        """Search mutations by genomic coordinates"""
        try:
            params = {
                "chr": chromosome,
                "pos": position,
                "ref": ref,
                "alt": alt
            }
            response = self.session.get(
                f"{self.base_url}/mutations",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"COSMIC coordinates API error: {e}")
            return {"error": str(e), "results": []}
    
    def get_mutation_details(self, cosmic_id: str) -> Dict[str, Any]:
        """Get detailed information for a specific COSMIC mutation"""
        try:
            response = self.session.get(
                f"{self.base_url}/mutations/{cosmic_id}",
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"COSMIC mutation details API error: {e}")
            return {"error": str(e)}
    
    def search_cancer_types(self, cancer_type: str) -> Dict[str, Any]:
        """Search for cancer types in COSMIC"""
        try:
            params = {"cancer_type": cancer_type, "limit": 50}
            response = self.session.get(
                f"{self.base_url}/cancer_types",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"COSMIC cancer types API error: {e}")
            return {"error": str(e), "results": []}


# Mock COSMIC client for demo purposes (when API key is not available)
class MockCOSMICClient(COSMICClient):
    """Mock COSMIC client that returns sample data for demonstration"""
    
    def search_mutations(self, gene: str, mutation: str = "", limit: int = 100) -> Dict[str, Any]:
        """Return mock mutation data"""
        return {
            "results": [
                {
                    "cosmic_id": f"COSM{12345 + hash(gene) % 1000}",
                    "gene": gene.upper(),
                    "mutation": mutation or "p.R175H",
                    "chromosome": "17",
                    "position": 7577120,
                    "reference": "G",
                    "alternate": "A",
                    "cancer_types": ["Breast", "Colon", "Lung"],
                    "frequency": 0.15,
                    "pathogenicity": "Pathogenic",
                    "clinical_significance": "Likely pathogenic"
                }
            ],
            "total": 1,
            "source": "COSMIC (Mock Data)"
        }
    
    def get_gene_info(self, gene: str) -> Dict[str, Any]:
        """Return mock gene information"""
        return {
            "gene": gene.upper(),
            "description": f"Tumor suppressor gene {gene.upper()}",
            "chromosome": "17",
            "start": 7574000,
            "end": 7590000,
            "strand": "+",
            "cosmic_id": f"GENE{hash(gene) % 10000}",
            "mutations_count": 1250,
            "cancer_types": ["Breast", "Colon", "Lung", "Pancreas"],
            "source": "COSMIC (Mock Data)"
        }
    
    def search_by_coordinates(self, chromosome: str, position: int, ref: str, alt: str) -> Dict[str, Any]:
        """Return mock coordinate-based search results"""
        return {
            "results": [
                {
                    "cosmic_id": f"COSM{12345 + hash(f'{chromosome}{position}') % 1000}",
                    "gene": "TP53",
                    "mutation": f"p.{ref}{position}{alt}",
                    "chromosome": chromosome,
                    "position": position,
                    "reference": ref,
                    "alternate": alt,
                    "cancer_types": ["Breast", "Colon"],
                    "frequency": 0.08,
                    "pathogenicity": "Pathogenic",
                    "clinical_significance": "Pathogenic"
                }
            ],
            "total": 1,
            "source": "COSMIC (Mock Data)"
        }
    
    def get_mutation_details(self, cosmic_id: str) -> Dict[str, Any]:
        """Return mock mutation details"""
        return {
            "cosmic_id": cosmic_id,
            "gene": "TP53",
            "mutation": "p.R175H",
            "chromosome": "17",
            "position": 7577120,
            "reference": "G",
            "alternate": "A",
            "cancer_types": ["Breast", "Colon", "Lung"],
            "frequency": 0.15,
            "pathogenicity": "Pathogenic",
            "clinical_significance": "Likely pathogenic",
            "drug_responses": ["Sensitive to PARP inhibitors"],
            "therapies": ["Olaparib", "Rucaparib"],
            "source": "COSMIC (Mock Data)"
        }
    
    def search_cancer_types(self, cancer_type: str) -> Dict[str, Any]:
        """Return mock cancer type search results"""
        return {
            "results": [
                {
                    "cancer_type": cancer_type,
                    "cosmic_id": f"CANCER{hash(cancer_type) % 1000}",
                    "mutations_count": 5000,
                    "genes_affected": 150,
                    "source": "COSMIC (Mock Data)"
                }
            ],
            "total": 1,
            "source": "COSMIC (Mock Data)"
        }


def get_cosmic_client(api_key: Optional[str] = None) -> COSMICClient:
    """Factory function to get COSMIC client (real or mock)"""
    if api_key:
        return COSMICClient(api_key)
    else:
        return MockCOSMICClient()
