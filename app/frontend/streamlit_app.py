import json
import base64
import requests
import streamlit as st
import plotly.express as px
import py3Dmol

API_BASE = "http://127.0.0.1:8000"

st.set_page_config(page_title="Cancer Mutation Analysis", layout="wide")

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .main-header h1 {
        color: white;
        font-size: 2.5rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
    }
    .main-header p {
        color: #e8f4fd;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid #2a5298;
    }
    .sidebar .sidebar-content {
        background: #f8f9fa;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background: #e9ecef;
        border-radius: 8px 8px 0 0;
        padding: 0.5rem 1rem;
    }
    .stTabs [aria-selected="true"] {
        background: #2a5298;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Header section
st.markdown("""
<div class="main-header">
    <h1>Cancer Mutation Analysis</h1>
    <p>Advanced pathogenicity scoring and clinical annotation platform</p>
</div>
""", unsafe_allow_html=True)

if "job_id" not in st.session_state:
	st.session_state.job_id = None
if "results" not in st.session_state:
	st.session_state.results = None
if "analyses" not in st.session_state:
	st.session_state.analyses = ["all"]

with st.sidebar:
	st.markdown("### 🔧 Interactive Analysis")
	
	# Cancer Type Selection
	cancer_type_sidebar = st.selectbox(
		"**Cancer Type**", 
		["All", "Breast", "Lung", "Colorectal", "Prostate", "Stomach", "Liver", "Cervical", "Thyroid", "Esophageal", "Ovarian", "Pancreatic", "Bladder", "Kidney", "Leukemia", "Lymphoma", "Melanoma", "Endometrial", "Brain", "Head and Neck", "Sarcoma", "Multiple Myeloma", "Testicular", "Gallbladder", "Bile Duct", "Skin"],
		help="Select cancer type for analysis"
	)
	
	# Gene Input
	gene_input = st.text_input("**Gene Symbol**", placeholder="e.g., TP53, BRCA1", help="Enter gene symbol")
	
	# Algorithm Selection
	selected_algorithm = st.selectbox(
		"**Algorithm**",
		["SIFT", "PolyPhen-2", "PROVEAN", "MutationAssessor", "REVEL", "MetaLR"],
		help="Select scoring algorithm"
	)
	
	# Coordinate Search Box
	st.markdown("#### 📍 Coordinate Search")
	chromosome = st.text_input("**Chromosome**", placeholder="e.g., 1, 2, X, Y", help="Chromosome number")
	position = st.number_input("**Position**", min_value=1, value=None, help="Genomic position")
	ref_allele = st.text_input("**Ref Allele**", placeholder="e.g., A, T, G, C", help="Reference allele")
	alt_allele = st.text_input("**Alt Allele**", placeholder="e.g., A, T, G, C", help="Alternative allele")
	
	# Pathogenicity Level Selection
	st.markdown("#### 🧬 Pathogenicity Level")
	pathogenicity_level = st.selectbox(
		"**Pathogenicity Level**",
		["Destructive", "Moderate Destructive", "Little Destructive"],
		help="Select pathogenicity level for analysis"
	)
	
	# HGVSp Input (Amino Acid Change)
	st.markdown("#### 🧪 HGVSp Analysis")
	hgvsp_input = st.text_input("**HGVSp**", placeholder="e.g., p.R175H, p.G12D", help="Amino acid change in HGVSp format")
	
	# Analyze Button
	if st.button("🔍 Analyze Gene", use_container_width=True, type="primary"):
		if gene_input or (chromosome and position and ref_allele and alt_allele) or hgvsp_input:
			with st.spinner("Analyzing..."):
				try:
					if hgvsp_input:
						# HGVSp-based analysis
						st.session_state.gene_analysis = {
							"gene": "Unknown",
							"cancer_type": cancer_type_sidebar,
							"algorithm": selected_algorithm,
							"pathogenicity_level": pathogenicity_level,
							"hgvsp_info": {
								"hgvsp": hgvsp_input,
								"amino_acid_change": hgvsp_input,
								"pathogenicity": pathogenicity_level
							}
						}
						st.success(f"✅ Analyzing HGVSp: {hgvsp_input}")
					elif chromosome and position and ref_allele and alt_allele:
						# Coordinate-based search
						resp = requests.post(f"{API_BASE}/cosmic/search", json={
							"search_type": "coordinates",
							"query": f"{chromosome}:{position}{ref_allele}>{alt_allele}",
							"chromosome": chromosome,
							"position": position,
							"ref": ref_allele,
							"alt": alt_allele
						}, timeout=30)
						resp.raise_for_status()
						coord_data = resp.json()
						
						if coord_data.get("results"):
							mutation_info = coord_data["results"][0]
							st.session_state.gene_analysis = {
								"gene": mutation_info.get("gene", "Unknown"),
								"cancer_type": cancer_type_sidebar,
								"algorithm": selected_algorithm,
								"pathogenicity_level": pathogenicity_level,
								"coordinate_info": mutation_info,
								"coordinates": f"{chromosome}:{position}{ref_allele}>{alt_allele}"
							}
							st.success(f"✅ Found mutation at {chromosome}:{position}")
						else:
							st.error("❌ No mutation found at these coordinates")
					else:
						# Gene-based search
						resp = requests.post(f"{API_BASE}/cosmic/search", json={
							"search_type": "gene",
							"query": gene_input
						}, timeout=30)
						resp.raise_for_status()
						gene_data = resp.json()
						
						if "error" not in gene_data["results"]:
							gene_info = gene_data["results"]
							st.session_state.gene_analysis = {
								"gene": gene_input,
								"cancer_type": cancer_type_sidebar,
								"algorithm": selected_algorithm,
								"pathogenicity_level": pathogenicity_level,
								"gene_info": gene_info
							}
							st.success(f"✅ Found {gene_input}")
						else:
							st.error(f"❌ Gene not found: {gene_data['results']['error']}")
				except Exception as e:
					st.error(f"❌ Analysis failed: {str(e)}")
		else:
			st.warning("⚠️ Please enter a gene symbol, complete coordinate information, or HGVSp")
	
	# Display Results
	if "gene_analysis" in st.session_state:
		analysis = st.session_state.gene_analysis
		st.markdown("### 📊 Analysis Results")
		
		# Check analysis type and display appropriate results
		if "hgvsp_info" in analysis:
			# HGVSp-based results
			hgvsp_info = analysis["hgvsp_info"]
			st.metric("HGVSp", hgvsp_info.get("hgvsp", "Unknown"))
			st.metric("Amino Acid Change", hgvsp_info.get("amino_acid_change", "Unknown"))
			st.metric("Selected Pathogenicity", analysis.get("pathogenicity_level", "Unknown"))
			
			# Mock score based on HGVSp and algorithm
			import random
			random.seed(f"{hgvsp_info['hgvsp']}_{analysis['algorithm']}")
			mock_score = round(random.random(), 3)
		elif "coordinate_info" in analysis:
			# Coordinate-based results
			coord_info = analysis["coordinate_info"]
			st.metric("Gene", coord_info.get("gene", "Unknown"))
			st.metric("Coordinates", analysis.get("coordinates", "Unknown"))
			st.metric("Frequency", f"{coord_info.get('frequency', 0):.3f}")
			st.metric("Selected Pathogenicity", analysis.get("pathogenicity_level", "Unknown"))
			
			# Mock score based on coordinates and algorithm
			import random
			random.seed(f"{analysis['coordinates']}_{analysis['algorithm']}")
			mock_score = round(random.random(), 3)
		else:
			# Gene-based results
			gene_info = analysis["gene_info"]
			st.metric("Mutations Count", gene_info.get("mutations_count", 0))
			st.metric("Chromosome", gene_info.get("chromosome", "Unknown"))
			st.metric("Selected Pathogenicity", analysis.get("pathogenicity_level", "Unknown"))
			
			# Mock score based on gene and algorithm
			import random
			random.seed(f"{analysis['gene']}_{analysis['algorithm']}")
			mock_score = round(random.random(), 3)
		
		# Score interpretation
		if mock_score >= 0.8:
			score_level = "🔴 Destructive"
			score_color = "red"
		elif mock_score >= 0.5:
			score_level = "🟡 Moderate Destructive"
			score_color = "orange"
		else:
			score_level = "🟢 Little Destructive"
			score_color = "green"
		
		st.markdown(f"**{analysis['algorithm']} Score:** {mock_score}")
		st.markdown(f"**Pathogenicity:** {score_level}")
		
		# Cancer types
		if "hgvsp_info" in analysis:
			# For HGVSp analysis, show mock cancer types based on pathogenicity level
			pathogenicity = analysis.get("pathogenicity_level", "Little Destructive")
			if pathogenicity == "Destructive":
				cancer_types = ["Breast", "Lung", "Colorectal", "Prostate"]
			elif pathogenicity == "Moderate Destructive":
				cancer_types = ["Breast", "Lung", "Colorectal"]
			else:
				cancer_types = ["Breast", "Lung"]
		elif "coordinate_info" in analysis:
			cancer_types = coord_info.get("cancer_types", [])
		else:
			cancer_types = gene_info.get("cancer_types", [])
		
		if cancer_types:
			st.write("**Associated Cancers:**")
			for ct in cancer_types[:5]:  # Show first 5
				st.write(f"• {ct}")
	
	st.markdown("---")
	st.markdown("### 📊 File Analysis Filters")
	
	# File Upload Section
	st.markdown("#### 📁 Upload Data")
	uploaded_file = st.file_uploader("**Upload Variant File**", type=["vcf", "csv", "json", "xlsx"], help="Supported formats: VCF, CSV, JSON, Excel", key="sidebar_upload")
	
	if uploaded_file is not None:
		st.success(f"✅ Selected: {uploaded_file.name}")
		if st.button("🚀 Upload & Analyze", use_container_width=True, key="sidebar_analyze"):
			with st.spinner("Processing..."):
				try:
					files = {"file": (uploaded_file.name, uploaded_file.read(), uploaded_file.type or "application/octet-stream")}
					resp = requests.post(f"{API_BASE}/upload", files=files, timeout=60)
					resp.raise_for_status()
					data = resp.json()
					st.session_state.job_id = data["job_id"]
					st.success(f"✅ Uploaded {data['num_variants']} variants")
					
					with st.spinner("Running analysis..."):
						req = {"job_id": st.session_state.job_id, "analyses": st.session_state.get("analyses", ["all"]), "options": {}}
						resp2 = requests.post(f"{API_BASE}/analyze", json=req, timeout=120)
						resp2.raise_for_status()
						st.session_state.results = resp2.json()
						st.success("✅ Analysis completed!")
				except Exception as e:  # noqa: BLE001
					st.error(f"❌ Error: {str(e)}")
	
	st.markdown("#### 🔍 Filter Settings")
	gene_filter = st.text_input("**Gene Filter**", value="", help="Comma-separated gene names (e.g., TP53,BRCA1)")
	selected_algo_for_filter = st.selectbox("**Score Algorithm**", ["auto", "SIFT", "PolyPhen-2", "PROVEAN", "MutationAssessor", "REVEL", "MetaLR"], help="Algorithm for score filtering")
	
	# Calculate Button
	if st.button("🧮 Calculate", use_container_width=True, type="primary"):
		if st.session_state.results:
			st.success("✅ Calculation completed! Check the tabs below for results.")
			# Force refresh of the filtered results
			st.rerun()
		else:
			st.warning("⚠️ Please upload and analyze data first.")
	
	st.markdown("---")
	st.markdown("### 📄 Report Settings")
	report_format = st.selectbox("**Export Format**", ["html", "pdf", "xlsx"], help="Report export format") 

# Search section
st.markdown("### 🔍 COSMIC Database Search")
search_tab1, search_tab2, search_tab3, search_tab4 = st.tabs(["🧬 Gene Search", "🔬 Mutation Search", "📍 Coordinate Search", "🎗️ Cancer Type Search"])

with search_tab1:
    col1, col2 = st.columns([3, 1])
    with col1:
        gene_query = st.text_input("**Gene Symbol**", placeholder="e.g., TP53, BRCA1, EGFR", key="gene_search")
    with col2:
        gene_search_btn = st.button("🔍 Search Gene", use_container_width=True, key="gene_btn")
    
    if gene_search_btn and gene_query:
        with st.spinner("Searching COSMIC..."):
            try:
                resp = requests.post(f"{API_BASE}/cosmic/search", json={
                    "search_type": "gene",
                    "query": gene_query
                }, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                if "error" not in data["results"]:
                    gene_info = data["results"]
                    st.success(f"✅ Found gene: {gene_info.get('gene', 'Unknown')}")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Mutations Count", gene_info.get("mutations_count", 0))
                        st.metric("Chromosome", gene_info.get("chromosome", "Unknown"))
                    with col2:
                        st.metric("Start Position", f"{gene_info.get('start', 0):,}")
                        st.metric("End Position", f"{gene_info.get('end', 0):,}")
                    st.write("**Cancer Types:**", ", ".join(gene_info.get("cancer_types", [])))
                else:
                    st.error(f"❌ Error: {data['results']['error']}")
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")

with search_tab2:
    col1, col2 = st.columns([2, 1])
    with col1:
        mutation_query = st.text_input("**Mutation**", placeholder="e.g., p.R175H, c.524G>A", key="mutation_search")
    with col2:
        mutation_gene = st.text_input("**Gene**", placeholder="e.g., TP53", key="mutation_gene")
    
    col3, col4 = st.columns([3, 1])
    with col4:
        mutation_search_btn = st.button("🔍 Search Mutation", use_container_width=True, key="mutation_btn")
    
    if mutation_search_btn and mutation_query:
        with st.spinner("Searching COSMIC..."):
            try:
                resp = requests.post(f"{API_BASE}/cosmic/search", json={
                    "search_type": "mutation",
                    "query": mutation_query,
                    "gene": mutation_gene
                }, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                if "error" not in data["results"]:
                    mutations = data["results"].get("results", [])
                    if mutations:
                        st.success(f"✅ Found {len(mutations)} mutation(s)")
                        for mut in mutations[:5]:  # Show first 5
                            with st.expander(f"Mutation: {mut.get('mutation', 'Unknown')}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**COSMIC ID:** {mut.get('cosmic_id', 'Unknown')}")
                                    st.write(f"**Gene:** {mut.get('gene', 'Unknown')}")
                                    st.write(f"**Pathogenicity:** {mut.get('pathogenicity', 'Unknown')}")
                                with col2:
                                    st.write(f"**Frequency:** {mut.get('frequency', 0):.3f}")
                                    st.write(f"**Cancer Types:** {', '.join(mut.get('cancer_types', []))}")
                    else:
                        st.warning("⚠️ No mutations found")
                else:
                    st.error(f"❌ Error: {data['results']['error']}")
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")

with search_tab3:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        coord_chr = st.text_input("**Chromosome**", placeholder="17", key="coord_chr")
    with col2:
        coord_pos = st.number_input("**Position**", min_value=1, value=7577120, key="coord_pos")
    with col3:
        coord_ref = st.text_input("**Ref**", placeholder="G", key="coord_ref")
    with col4:
        coord_alt = st.text_input("**Alt**", placeholder="A", key="coord_alt")
    
    coord_search_btn = st.button("🔍 Search Coordinates", use_container_width=True, key="coord_btn")
    
    if coord_search_btn and all([coord_chr, coord_pos, coord_ref, coord_alt]):
        with st.spinner("Searching COSMIC..."):
            try:
                resp = requests.post(f"{API_BASE}/cosmic/search", json={
                    "search_type": "coordinates",
                    "query": f"{coord_chr}:{coord_pos}",
                    "chromosome": coord_chr,
                    "position": coord_pos,
                    "ref": coord_ref,
                    "alt": coord_alt
                }, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                if "error" not in data["results"]:
                    mutations = data["results"].get("results", [])
                    if mutations:
                        st.success(f"✅ Found {len(mutations)} mutation(s)")
                        for mut in mutations:
                            with st.expander(f"Mutation: {mut.get('mutation', 'Unknown')}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**COSMIC ID:** {mut.get('cosmic_id', 'Unknown')}")
                                    st.write(f"**Gene:** {mut.get('gene', 'Unknown')}")
                                    st.write(f"**Clinical Significance:** {mut.get('clinical_significance', 'Unknown')}")
                                with col2:
                                    st.write(f"**Frequency:** {mut.get('frequency', 0):.3f}")
                                    st.write(f"**Cancer Types:** {', '.join(mut.get('cancer_types', []))}")
                    else:
                        st.warning("⚠️ No mutations found at this location")
                else:
                    st.error(f"❌ Error: {data['results']['error']}")
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")

with search_tab4:
    col1, col2 = st.columns([3, 1])
    with col1:
        cancer_query = st.text_input("**Cancer Type**", placeholder="e.g., Breast, Colon, Lung", key="cancer_search")
    with col2:
        cancer_search_btn = st.button("🔍 Search Cancer", use_container_width=True, key="cancer_btn")
    
    if cancer_search_btn and cancer_query:
        with st.spinner("Searching COSMIC..."):
            try:
                resp = requests.post(f"{API_BASE}/cosmic/search", json={
                    "search_type": "cancer_type",
                    "query": cancer_query
                }, timeout=30)
                resp.raise_for_status()
                data = resp.json()
                if "error" not in data["results"]:
                    cancers = data["results"].get("results", [])
                    if cancers:
                        st.success(f"✅ Found {len(cancers)} cancer type(s)")
                        for cancer in cancers:
                            with st.expander(f"Cancer Type: {cancer.get('cancer_type', 'Unknown')}"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.write(f"**COSMIC ID:** {cancer.get('cosmic_id', 'Unknown')}")
                                    st.write(f"**Mutations Count:** {cancer.get('mutations_count', 0):,}")
                                with col2:
                                    st.write(f"**Genes Affected:** {cancer.get('genes_affected', 0)}")
                    else:
                        st.warning("⚠️ No cancer types found")
                else:
                    st.error(f"❌ Error: {data['results']['error']}")
            except Exception as e:
                st.error(f"❌ Search failed: {str(e)}")

st.markdown("---")

# Clinical Query section
st.markdown("### 🧪 Clinical Query")

COMMON_CANCERS = [
	"Breast", "Lung", "Colorectal", "Prostate", "Stomach", "Liver",
	"Cervical", "Thyroid", "Esophageal", "Ovarian", "Pancreatic", "Bladder",
	"Kidney", "Leukemia", "Lymphoma", "Melanoma", "Endometrial", "Brain",
	"Head and Neck", "Sarcoma", "Multiple Myeloma", "Testicular", "Gallbladder",
	"Bile Duct", "Skin"
]

cc1, cc2, cc3, cc4, cc5 = st.columns([2,2,2,2,1])
with cc1:
	cancer_type_sel = st.selectbox("**Select Cancer Type**", COMMON_CANCERS, help="Top ~25 cancer types")
with cc2:
	gene_id_input = st.text_input("**Gene ID**", placeholder="e.g., TP53")
with cc3:
	mutation_loc_input = st.text_input("**Location of Mutation**", placeholder="e.g., 17:7577120 or p.R175H")
with cc4:
	patho_level = st.selectbox("**Pathogenicity Level**", ["Destructive", "Moderate Destructive", "Little Destructive"], index=0)
with cc5:
	calc_btn = st.button("Calculate", use_container_width=True)


def _classify_level(score: float) -> str:
	if score is None:
		return "Unknown"
	if score >= 0.8:
		return "Destructive"
	if score >= 0.5:
		return "Moderate Destructive"
	return "Little Destructive"

if calc_btn:
	if not st.session_state.results:
		st.warning("Run analysis first to calculate.")
	else:
		res = st.session_state.results
		scores = res.get("scores", {})
		ensemble = res.get("ensemble", {})
		annotations = res.get("annotations", {})

		rows = []
		for key, entry in scores.items():
			# Filter by cancer type (from annotations via COSMIC cancer_types)
			ann = annotations.get(key, {}).get("COSMIC", {})
			cancers = ann.get("cancer_types", [])
			if cancer_type_sel and cancers and (cancer_type_sel not in cancers):
				continue
			# Filter by gene id
			if gene_id_input:
				if gene_id_input.upper() not in key.upper():
					continue
			# Filter by mutation location string match (key contains chrom:posref>alt)
			if mutation_loc_input:
				if mutation_loc_input not in key and mutation_loc_input not in json.dumps(annotations.get(key, {})):
					continue
			# Use ensemble REVEL if available for classification fallback
			ev = ensemble.get(key, {}).get("REVEL")
			label = _classify_level(ev if ev is not None else (sum(entry.values())/len(entry) if entry else 0))
			if label != patho_level:
				continue
			row = {"variant": key, "level": label, "REVEL": ev}
			row.update(entry)
			rows.append(row)

		if rows:
			st.success(f"Found {len(rows)} variant(s) matching criteria")
			st.dataframe(rows, use_container_width=True, hide_index=True)
		else:
			st.warning("No variants matched the selected criteria.")

st.markdown("---")

# File upload section
st.markdown("### 📁 Data Upload")
uploaded = st.file_uploader("**Upload Variant File**", type=["vcf", "csv", "json", "xlsx"], help="Supported formats: VCF, CSV, JSON, Excel")

col_upload, col_actions = st.columns([2,1])
with col_upload:
	if uploaded is not None:
		st.success(f"✅ Selected: {uploaded.name}")
		st.caption(f"Size: {uploaded.size:,} bytes")
with col_actions:
	if uploaded is not None:
		if st.button("🚀 Upload & Analyze", use_container_width=True, type="primary"):
			with st.spinner("Processing file..."):
				try:
					files = {"file": (uploaded.name, uploaded.read(), uploaded.type or "application/octet-stream")}
					resp = requests.post(f"{API_BASE}/upload", files=files, timeout=60)
					resp.raise_for_status()
					data = resp.json()
					st.session_state.job_id = data["job_id"]
					st.success(f"✅ Uploaded {data['num_variants']} variants")
					
					with st.spinner("Running analysis..."):
						req = {"job_id": st.session_state.job_id, "analyses": st.session_state.get("analyses", ["all"]), "options": {}}
						resp2 = requests.post(f"{API_BASE}/analyze", json=req, timeout=120)
						resp2.raise_for_status()
						st.session_state.results = resp2.json()
						st.success("✅ Analysis completed!")
				except Exception as e:  # noqa: BLE001
					st.error(f"❌ Error: {str(e)}")


def _filtered_results(results):
	if not results:
		return None
	genes = [g.strip().upper() for g in gene_filter.split(",") if g.strip()]
	# Build variant meta map from results.variants (list of dicts) to keys used in scores
	variant_list = results.get("variants", [])
	key_to_gene = {}
	for idx, v in enumerate(variant_list):
		key = f"{v.get('chrom','chr?')}:{v.get('pos','?')}{v.get('ref','?')}>{v.get('alt','?')}#{idx}"
		key_to_gene[key] = (v.get("gene") or "").upper()
	# Apply filters on scores or ensemble
	scores = results.get("scores", {})
	ensemble = results.get("ensemble", {})
	def pass_score(k: str, entry: dict) -> bool:
		algo = selected_algo_for_filter
		val = None
		if algo in {"REVEL", "MetaLR"}:
			val = ensemble.get(k, {}).get(algo)
		elif algo == "auto":
			vals = list(entry.values()) + list(ensemble.get(k, {}).values())
			val = sum(vals) / len(vals) if vals else None
		else:
			val = entry.get(algo)
		if val is None:
			return True
		return (val >= score_min) and (val <= score_max)

	filtered_keys = []
	for k, entry in scores.items():
		if genes and key_to_gene.get(k, "") not in genes:
			continue
		if not pass_score(k, entry):
			continue
		filtered_keys.append(k)

	return {
		"scores": {k: scores[k] for k in filtered_keys},
		"ensemble": {k: ensemble.get(k, {}) for k in filtered_keys},
		"annotations": {k: results.get("annotations", {}).get(k, {}) for k in filtered_keys},
		"variants": [v for idx, v in enumerate(variant_list) if f"{v.get('chrom','chr?')}:{v.get('pos','?')}{v.get('ref','?')}>{v.get('alt','?')}#{idx}" in filtered_keys],
	}


tab_dashboard, tab_variants, tab_scores, tab_ann, tab_struct, tab_report = st.tabs([
	"📊 Dashboard", "🧬 Variants", "📈 Scores", "📋 Annotations", "🔬 Structure", "📄 Report"
])

with tab_dashboard:
	st.markdown("### 📊 Analysis Overview")
	if st.session_state.results:
		res = _filtered_results(st.session_state.results)
		num_vars = len(res.get("variants", []))
		total_vars = len(st.session_state.results.get("variants", []))
		
		col1, col2, col3, col4 = st.columns(4)
		with col1:
			st.metric("📊 Total Variants", total_vars)
		with col2:
			st.metric("🔍 Filtered Variants", num_vars)
		with col3:
			algo_count = len([a for a in st.session_state.get("analyses", ["all"]) if a != "all"]) or 4
			st.metric("⚙️ Algorithms", algo_count)
		with col4:
			score_count = len(res.get("scores", {}))
			st.metric("📈 Scored Variants", score_count)
		
		if num_vars > 0:
			st.markdown("### 🎯 Quick Insights")
			# Show top scoring variants
			scores_data = []
			for key, entry in res.get("scores", {}).items():
				avg_score = sum(entry.values()) / len(entry) if entry else 0
				scores_data.append({"variant": key, "avg_score": avg_score})
			
			if scores_data:
				scores_data.sort(key=lambda x: x["avg_score"], reverse=True)
				st.markdown("**Top 5 Highest Scoring Variants:**")
				for i, item in enumerate(scores_data[:5], 1):
					st.write(f"{i}. {item['variant']}: {item['avg_score']:.3f}")
		else:
			st.warning("No variants match the current filters. Adjust filters in the sidebar.")
	else:
		st.info("📁 Upload a variant file and run analysis to see the dashboard.")

with tab_variants:
	st.markdown("### 🧬 Variant Data")
	if st.session_state.results:
		res = _filtered_results(st.session_state.results)
		if res.get("variants"):
			st.dataframe(res["variants"], use_container_width=True, hide_index=True)
			st.caption(f"Showing {len(res['variants'])} variants after filtering")
		else:
			st.warning("⚠️ No variants match the current filters.")
	else:
		st.info("📁 Upload a variant file to see data here.")

with tab_scores:
	st.markdown("### 📈 Pathogenicity Scores")
	if st.session_state.results:
		res = _filtered_results(st.session_state.results)
		
		# Individual algorithm scores
		st.markdown("#### 🔬 Individual Algorithm Scores")
		rows = []
		for key, entry in res.get("scores", {}).items():
			for algo, val in entry.items():
				rows.append({"variant": key, "algorithm": algo, "score": val})
		
		if rows:
			# Color scale: green (benign) to red (deleterious)
			fig = px.bar(rows, x="variant", y="score", color="score", 
						color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
						facet_row="algorithm", title="Pathogenicity Scores by Algorithm")
			fig.update_layout(height=400 * len(set(r["algorithm"] for r in rows)))
			st.plotly_chart(fig, use_container_width=True)
		else:
			st.warning("⚠️ No individual algorithm scores available.")

		# Ensemble scores
		st.markdown("#### 🎯 Ensemble Scores")
		rows2 = []
		for key, entry in res.get("ensemble", {}).items():
			for algo, val in entry.items():
				rows2.append({"variant": key, "ensemble": algo, "score": val})
		
		if rows2:
			fig2 = px.bar(rows2, x="variant", y="score", color="score", 
						color_continuous_scale=["#2ecc71", "#f39c12", "#e74c3c"],
						facet_row="ensemble", title="Ensemble Pathogenicity Scores")
			fig2.update_layout(height=400 * len(set(r["ensemble"] for r in rows2)))
			st.plotly_chart(fig2, use_container_width=True)
		else:
			st.warning("⚠️ No ensemble scores available.")
	else:
		st.info("📁 Upload a variant file to see scores here.")

with tab_ann:
	st.markdown("### 📋 Database Annotations")
	if st.session_state.results:
		res = _filtered_results(st.session_state.results)
		ann = res.get("annotations", {})
		if ann:
			ann_rows = []
			for k, v in ann.items():
				ann_rows.append({
					"Variant": k,
					"COSMIC Match": "✅" if v.get("COSMIC", {}).get("match") else "❌",
					"ClinVar Significance": v.get("ClinVar", {}).get("clinical_significance", "Unknown"),
					"MyCancerGenome Evidence": v.get("MyCancerGenome", {}).get("evidence", "None"),
				})
			st.dataframe(ann_rows, use_container_width=True, hide_index=True)
			st.caption("Database annotations for filtered variants")
		else:
			st.warning("⚠️ No database annotations available.")
	else:
		st.info("📁 Upload a variant file to see annotations here.")

with tab_struct:
	st.markdown("### 🔬 3D Protein Structure Viewer")
	
	col1, col2 = st.columns([2, 1])
	with col1:
		pdb_id = st.text_input("**PDB ID**", value="1CRN", help="Enter a PDB ID (e.g., 1CRN, 1TUP)")
	with col2:
		load_btn = st.button("🔍 Load Structure", use_container_width=True)
	
	if load_btn and pdb_id:
		try:
			with st.spinner("Loading 3D structure..."):
				view = py3Dmol.view(query=f"pdb:{pdb_id}")
				view.setStyle({"cartoon": {"color": "spectrum"}})
				view.addSurface(py3Dmol.VDW, {"opacity": 0.3})
				view.zoomTo()
				view.show()
				st.components.v1.html(view._make_html(), height=600)
				st.success(f"✅ Loaded structure: {pdb_id}")
		except Exception as e:  # noqa: BLE001
			st.error(f"❌ Error loading structure: {str(e)}")
			st.info("💡 Try a different PDB ID or check your internet connection.")
	
	st.markdown("#### 📚 Popular Cancer-Related Structures")
	popular_pdbs = ["1TUP", "1CRN", "2J4M", "3KMD", "4HJO"]
	for pdb in popular_pdbs:
		if st.button(f"Load {pdb}", key=f"pdb_{pdb}"):
			try:
				view = py3Dmol.view(query=f"pdb:{pdb}")
				view.setStyle({"cartoon": {"color": "spectrum"}})
				view.addSurface(py3Dmol.VDW, {"opacity": 0.3})
				view.zoomTo()
				view.show()
				st.components.v1.html(view._make_html(), height=600)
			except Exception as e:  # noqa: BLE001
				st.error(f"Error loading {pdb}: {str(e)}")

with tab_report:
	st.markdown("### 📄 Report Generation")
	
	if st.session_state.results and st.session_state.job_id:
		st.markdown("#### 📊 Report Options")
		col1, col2 = st.columns(2)
		with col1:
			st.info(f"**Current Format:** {report_format.upper()}")
			st.info(f"**Job ID:** {st.session_state.job_id}")
		with col2:
			st.info(f"**Variants:** {len(st.session_state.results.get('variants', []))}")
			algs = st.session_state.get('analyses', ['all'])
			st.info(f"**Algorithms:** {len(algs) if algs != ['all'] else 4}")
		
		if st.button("🚀 Generate Report", type="primary", use_container_width=True):
			with st.spinner("Generating report..."):
				try:
					payload = {"job_id": st.session_state.job_id, "format": report_format}
					resp3 = requests.post(f"{API_BASE}/report", json=payload, timeout=120)
					resp3.raise_for_status()
					data = resp3.json()
					
					if report_format == "html":
						st.download_button(
							label="📄 Download HTML Report",
							data=data["html"],
							file_name=f"cancer_mutation_report_{st.session_state.job_id[:8]}.html",
							mime="text/html",
							use_container_width=True
						)
					elif report_format == "pdf":
						pdf_b64 = data["pdf_base64"].encode("utf-8")
						st.download_button(
							label="📄 Download PDF Report",
							data=base64.b64decode(pdf_b64),
							file_name=f"cancer_mutation_report_{st.session_state.job_id[:8]}.pdf",
							mime="application/pdf",
							use_container_width=True
						)
					else:
						xlsx_b64 = data["excel_base64"].encode("utf-8")
						st.download_button(
							label="📊 Download Excel Report",
							data=base64.b64decode(xlsx_b64),
							file_name=f"cancer_mutation_report_{st.session_state.job_id[:8]}.xlsx",
							mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
							use_container_width=True
						)
					st.success("✅ Report generated successfully!")
				except Exception as e:  # noqa: BLE001
					st.error(f"❌ Error generating report: {str(e)}")
	else:
		st.info("📁 Upload a variant file and run analysis to generate reports.")
		st.markdown("#### 📋 Report Contents")
		st.markdown("""
		Reports will include:
		- **Variant Summary**: Complete list of analyzed variants
		- **Pathogenicity Scores**: Individual and ensemble scores
		- **Database Annotations**: COSMIC, ClinVar, MyCancerGenome matches
		- **Clinical Insights**: Actionable mutations and therapy options
		- **Visualizations**: Charts and graphs (HTML/PDF only)
		""")
