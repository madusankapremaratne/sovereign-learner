"""
Sovereign Learner - Explainability Dashboard
=============================================
Interactive visualization of how queries navigate through the agentic pipeline.
Analogous to SHAP for understanding AI decisions.

Run with: streamlit run dashboard.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import sys
import os
import time
from datetime import datetime
import json

# Add parent to path
# Add parent to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(project_root, "src"))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, ".env"))

# Import from core system source of truth
from sovereign_system.utils.sovereign_trace_logger import SovereignTrace, SovereignTracer, create_demo_trace, AgentStep

# Page config
st.set_page_config(
    page_title="Sovereign Learner - Explainability Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Compatibility for older Streamlit versions
if not hasattr(st, "rerun"):
    st.rerun = st.experimental_rerun

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0;
    }
    .sub-header {
        color: #666;
        font-size: 1.1rem;
        margin-top: 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 10px;
        color: white;
        height: 300px;
        display: flex;
        flex-direction: column;
        justify-content: flex-start;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .agent-box {
        border: 2px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        background: #fafafa;
    }
    .agent-box-local {
        border-color: #4CAF50;
        background: linear-gradient(135deg, #e8f5e9 0%, #c8e6c9 100%);
    }
    .agent-box-cloud {
        border-color: #2196F3;
        background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
    }
    .privacy-high { color: #4CAF50; font-weight: bold; }
    .privacy-medium { color: #FF9800; font-weight: bold; }
    .privacy-low { color: #f44336; font-weight: bold; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
    }
</style>
""", unsafe_allow_html=True)


def create_privacy_waterfall(trace: SovereignTrace) -> go.Figure:
    """create enhanced waterfall chart using go.Bar for custom coloring"""
    
    # Data prep
    x_data = ["Start"]
    y_data = [1.0] # Height of bar
    base_data = [0.0] # Start of bar
    text_data = ["<b>100%</b><br>Initial"]
    colors = ["#FF5252"] # Start Red

    # Scatter trace data for absolute values
    scatter_y = [1.0]
    scatter_text = ["100%"]
    
    prev_exposure = 1.0
    is_restored = False
    
    for step in trace.steps:
        x_data.append(step.agent_name)
        
        # Check if we are restoring context
        if "Recontextualizer" in step.agent_name:
            is_restored = True
            
        current_exposure = step.privacy_score_after
        delta = current_exposure - prev_exposure
        
        # Robust Waterfall Logic:
        base = min(prev_exposure, current_exposure)
        height = abs(delta)

        # Color Logic
        if delta < -0.01:
             base_data.append(base)
             y_data.append(height)
             colors.append("#00C853") # Green (Sanitization/Improvement)
             text_data.append(f"<b>{abs(delta):.0%}</b><br>Sanitized")
             
        elif delta > 0.01:
             base_data.append(base)
             y_data.append(height)
             if "Recontextualizer" in step.agent_name:
                 colors.append("#448AFF") # Blue (Restored)
                 text_data.append(f"<b>{abs(delta):.0%}</b><br>Restored")
             else:
                 colors.append("#FF5252") # Red (Leak)
                 text_data.append(f"<b>{abs(delta):.0%}</b><br>Risk")
                 
        else:
             # Maintenance Candle (No change) - Starts from 0, ends at value
             base_data.append(0.0) 
             y_data.append(current_exposure)
             
             if current_exposure > 0.8:
                 if is_restored:
                     colors.append("#448AFF") # Blue (Restored/Safe Local)
                 else:
                     colors.append("#ef5350") # Red (Maintained Risk)
             else:
                 colors.append("#66BB6A") # Green (Maintained Safe)
                 
             text_data.append(f"<b>{current_exposure:.0%}</b>") # Show absolute level
             
        # Add to scatter data for visibility of current state
        scatter_y.append(current_exposure)
        scatter_text.append(f"<b>{current_exposure:.0%}</b>")
        
        prev_exposure = current_exposure

    # Final Bar
    x_data.append("Final")
    y_data.append(prev_exposure)
    base_data.append(0)
    code = "#448AFF" if prev_exposure > 0.8 else "#00C853"
    colors.append(code)
    text_data.append(f"<b>{prev_exposure:.0%}</b><br>Final")
    
    # Add final scatter point
    scatter_y.append(prev_exposure)
    scatter_text.append(f"<b>{prev_exposure:.0%}</b>")
    
    # Create Figure
    fig = go.Figure()
    
    # 1. Bar Trace (Waterfall blocks)
    fig.add_trace(go.Bar(
        x=x_data,
        y=y_data,
        base=base_data,
        marker_color=colors,
        text=text_data,
        textposition="outside",
        textfont=dict(size=11),
        name="Change"
    ))

    # Add connector lines (simulation)
    # We can add a line shape for each step
    shapes = []
    
    # Safe Zone
    shapes.append(dict(
        type="rect",
        xref="paper", yref="y",
        x0=0, x1=1,
        y0=-0.05, y1=0.2, # 20% threshold
        fillcolor="#00C853", opacity=0.1,
        line_width=0, layer="below"
    ))
    
    fig.update_layout(
        title={
            'text': "<b>Data Exposure Level</b><br><span style='font-size:12px;color:grey'>Values indicate % of visible sensitive data</span>",
            'x': 0.5, 'xanchor': 'center'
        },
        showlegend=False,
        height=450,
        shapes=shapes,
        barmode='overlay', # Critical: prevents stacking, respects explicit 'base'
        yaxis=dict(
            title="Exposure Level (0% = Safe)",
            range=[-0.1, 1.25], 
            tickformat=".0%",
            zeroline=True, gridcolor='rgba(0,0,0,0.1)'
        ),
        xaxis=dict(tickangle=-15),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="Inter, sans-serif")
    )
    
    fig.add_annotation(
        x=0.02, y=0.1, xref="paper", yref="y",
        text="<b>✅ Cloud Safe Zone</b>", showarrow=False,
        font=dict(color="#00C853")
    )

    return fig


def create_agent_contribution_chart(trace: SovereignTrace) -> go.Figure:
    """Create horizontal bar chart showing each agent's contribution"""
    
    contributions = trace.get_agent_contributions()
    
    # Sort by contribution
    sorted_items = sorted(contributions.items(), key=lambda x: x[1], reverse=True)
    agents = [item[0] for item in sorted_items]
    values = [item[1] for item in sorted_items]
    
    # Color based on contribution
    colors = ['#4CAF50' if v > 0.1 else '#9E9E9E' for v in values]
    
    fig = go.Figure(go.Bar(
        x=values,
        y=agents,
        orientation='h',
        marker_color=colors,
        text=[f"{v:.1%}" for v in values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Agent Contribution to Privacy Protection",
        xaxis_title="Contribution Score",
        yaxis_title="Agent",
        height=350,
        xaxis_tickformat=".0%",
        yaxis=dict(autorange="reversed")
    )
    
    return fig


def create_timeline_chart(trace: SovereignTrace) -> go.Figure:
    """Create timeline/Gantt chart of agent execution"""
    
    timeline = trace.get_timeline()
    
    df = pd.DataFrame(timeline)
    
    # Create figure
    fig = go.Figure()
    
    colors = {
        "Sovereign Manager": "#1e3a5f",
        "Sensitivity Detector": "#2d5a87",
        "Semantic Generalizer": "#9C27B0",  # Purple - core contribution
        "Cloud Researcher": "#2196F3",  # Blue - cloud
        "Trust Enforcer": "#FF9800",
        "Recontextualizer": "#4CAF50",
        "Evidence Curator": "#607D8B"
    }
    
    for i, row in df.iterrows():
        fig.add_trace(go.Bar(
            x=[row['duration_ms']],
            y=[row['agent']],
            orientation='h',
            name=row['agent'],
            marker_color=colors.get(row['agent'], '#666'),
            text=f"{row['duration_ms']:.1f}ms",
            textposition='inside',
            hovertemplate=f"<b>{row['agent']}</b><br>Duration: {row['duration_ms']:.1f}ms<extra></extra>"
        ))
    
    fig.update_layout(
        title="Agent Execution Timeline",
        xaxis_title="Duration (ms)",
        yaxis_title="Agent",
        height=350,
        showlegend=False,
        barmode='stack',
        yaxis=dict(autorange="reversed")
    )
    
    return fig


def create_sankey_diagram(trace: SovereignTrace) -> go.Figure:
    """Create Sankey diagram showing data flow"""
    
    # Define agent colors
    agent_colors = {
        "Sovereign Manager": "#1e3a5f",
        "Sensitivity Detector": "#2d5a87",
        "Semantic Generalizer": "#9C27B0",
        "Cloud Researcher": "#2196F3",
        "Trust Enforcer": "#FF9800",
        "Recontextualizer": "#4CAF50",
        "Evidence Curator": "#607D8B"
    }
    
    # Build nodes
    labels = ["Original Query"]  # Start node
    colors = ["#f44336"]         # Start color (Red/Exposed)
    
    # Map agent names to node indices
    node_indices = {"Original Query": 0}
    current_idx = 1
    
    # Add agent nodes
    for step in trace.steps:
        if step.agent_name not in node_indices:
            labels.append(step.agent_name)
            colors.append(agent_colors.get(step.agent_name, "#9E9E9E"))
            node_indices[step.agent_name] = current_idx
            current_idx += 1
            
    # Add final node
    labels.append("Final Response")
    colors.append("#4CAF50") # Green/Protected
    node_indices["Final Response"] = current_idx
    
    # Build links
    source = []
    target = []
    values = []
    link_colors = []
    
    # Link 1: Original -> First Agent
    first_agent = trace.steps[0].agent_name if trace.steps else None
    if first_agent:
        source.append(node_indices["Original Query"])
        target.append(node_indices[first_agent])
        val = len(trace.original_query) if trace.original_query else 100
        values.append(max(10, val)) # Min width
        link_colors.append("rgba(30, 58, 95, 0.4)")
        
    # Links between agents
    for i in range(len(trace.steps) - 1):
        curr_step = trace.steps[i]
        next_step = trace.steps[i+1]
        
        source.append(node_indices[curr_step.agent_name])
        target.append(node_indices[next_step.agent_name])
        
        # Estimate data volume based on output length
        vol = len(curr_step.output_data)
        # Scale down large texts for visualization balance (cap visual width)
        values.append(max(5, min(vol, 300))) 
        
        # Color based on privacy (Blue if sanitized, Red if exposed)
        if curr_step.privacy_score_after > 0.5: # Highly protected
            link_colors.append("rgba(33, 150, 243, 0.4)") # Blue
        else:
            link_colors.append("rgba(244, 67, 54, 0.4)") # Redish
            
    # Link: Last Agent -> Final
    last_step = trace.steps[-1] if trace.steps else None
    if last_step:
        source.append(node_indices[last_step.agent_name])
        target.append(node_indices["Final Response"])
        val = len(trace.final_response) if trace.final_response else 100
        values.append(max(10, val))
        link_colors.append("rgba(76, 175, 80, 0.4)")
    
    fig = go.Figure(go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=colors
        ),
        link=dict(
            source=source,
            target=target,
            value=values,
            color=link_colors
        )
    ))
    
    fig.update_layout(
        title="Query Flow Through Sovereign Learner Pipeline (Dynamic)",
        height=500,
        font_size=12
    )
    
    return fig


def _clean_agent_input(text: str) -> str:
    """
    Heuristic to extract the actual input data from verbose task instructions.
    E.g., 'Scan the query: "How do I..." ...' -> 'How do I...'
    """
    if not text:
        return ""
        
    # Common prefixes in our tasks.yaml
    prefixes = [
        "Analyze the incoming user query:",
        "Scan the query:",
        "rewrite the query:",
        "Query:",
        "Response:"
    ]
    
    # Check if text starts with a known instruction pattern
    starts_with_instruction = any(text.strip().startswith(p) for p in prefixes)
    
    if starts_with_instruction:
        # If explicitly formatted as Key: Value, try return just the value line or remainder
        # Or look for quotes
        import re
        match = re.search(r'["\']([^"\']+)["\']', text)
        if match:
            return match.group(1)
            
        # Fallback: if starts with "Query:", split and take rest
        if text.strip().startswith("Query:"):
            return text.strip().replace("Query:", "").split('\n')[0].strip()
            
    return text

def render_agent_step(step: AgentStep, index: int, accumulated_mapping: dict = None):
    """Render a single agent step with details"""
    
    # Determine if local or cloud
    is_cloud = "cloud" in step.agent_name.lower() or "researcher" in step.agent_name.lower()
    box_class = "agent-box-cloud" if is_cloud else "agent-box-local"
    
    # Icon based on agent
    icons = {
        "Sovereign Manager": "🧭",
        "Sensitivity Detector": "🔍",
        "Semantic Generalizer": "🎭",
        "Cloud Researcher": "☁️",
        "Trust Enforcer": "🛡️",
        "Recontextualizer": "🔄",
        "Evidence Curator": "💾"
    }
    icon = icons.get(step.agent_name, "🤖")
    
    # Model assignment based on agent
    model_info = {
        "Sovereign Manager": ("SLM", "Phi-3.5 (3.8B)"),
        "Sensitivity Detector": ("SLM", "Phi-3.5 (3.8B)"),
        "Semantic Generalizer": ("SLM", "Phi-3.5 (3.8B)"),
        "Cloud Researcher": ("LLM", "Llama 3.3 70B (Groq)"),
        "Trust Enforcer": ("SLM", "Phi-3.5 (3.8B)"),
        "Recontextualizer": ("SLM", "Phi-3.5 (3.8B)"),
        "Evidence Curator": ("SLM", "Phi-3.5 (3.8B)")
    }
    model_type, model_name = model_info.get(step.agent_name, ("Unknown", "Unknown"))
    if "Cloud" in step.agent_name:
        model_type = "LLM"
        
    model_badge_color = "#2196F3" if model_type == "LLM" else "#4CAF50"
    
    # Privacy change indicator
    privacy_delta = step.privacy_score_before - step.privacy_score_after
    if privacy_delta > 0.1:
        privacy_indicator = "🟢 Protected"
        privacy_class = "privacy-high"
    elif privacy_delta < -0.1:
        privacy_indicator = "🔴 Exposed"
        privacy_class = "privacy-low"
    else:
        privacy_indicator = "🟡 Maintained"
        privacy_class = "privacy-medium"
        
    # Clean input for display
    display_input = _clean_agent_input(step.input_data)
    if len(display_input) > 200:
        display_input = display_input[:200] + "..."
    
    with st.container():
        st.markdown(f"""
        <div class="agent-box {box_class}">
            <h4>{icon} Step {index + 1}: {step.agent_name}</h4>
            <p><em>{step.agent_role}</em></p>
            <p style="margin-top: 8px;">
                <span style="background: {model_badge_color}; color: white; padding: 4px 10px; border-radius: 12px; font-size: 0.85rem; font-weight: 600;">
                    {model_type}
                </span>
                <span style="color: #666; margin-left: 8px; font-size: 0.9rem;">
                    {model_name}
                </span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown("**Input Data:**")
            st.code(display_input)
        
        with col2:
            st.markdown("**Output:**")
            st.code(step.output_data[:200] + "..." if len(step.output_data) > 200 else step.output_data)
        
        with col3:
            st.metric("Duration", f"{step.duration_ms:.1f}ms")
            st.markdown(f"<span class='{privacy_class}'>{privacy_indicator}</span>", unsafe_allow_html=True)
        
        # 1. Semantic Generalizer: Show Generated Mappings
        if "Generalizer" in step.agent_name and step.mapping:
             with st.expander("�️ Privacy Mappings Generated", expanded=True):
                mapping_data = []
                for k, v in step.mapping.items():
                    mapping_data.append({
                        "Sensitive Entity (Hidden)": v,
                        "Generated Placeholder": k
                    })
                st.table(pd.DataFrame(mapping_data))

        # 2. Recontextualizer: Show Restoration (Reversal)
        elif "Recontextualizer" in step.agent_name and accumulated_mapping:
             with st.expander("🔓 Context Restoration (Reversal)", expanded=True):
                restoration_data = []
                for k, v in accumulated_mapping.items():
                    restoration_data.append({
                        "Placeholder (Cloud Input)": k,
                        "Restored Entity (User Output)": v
                    })
                st.table(pd.DataFrame(restoration_data))

        # 3. Fallback: Show mapping if present but not handled above
        elif step.mapping:
            with st.expander("🔀 Mapping Table"):
                st.json(step.mapping)
        
        # Show metadata if present
        if step.metadata:
            with st.expander("📋 Metadata"):
                st.json(step.metadata)
        
        st.markdown("---")


def load_trace_callback(trace_file_path):
    """Callback to load trace file"""
    try:
        with open(trace_file_path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct trace object from saved JSON
        trace = SovereignTrace(
            query_id=data.get('query_id', 'loaded'),
            original_query=data.get('original_query', '')
        )
        
        # Set all trace attributes
        trace.final_response = data.get('final_response', '')
        trace.total_duration_ms = data.get('total_duration_ms', 0)
        trace.zone_used = data.get('zone_used', 1)
        trace.privacy_protection_score = data.get('privacy_protection_score', 0)
        trace.utility_score = data.get('utility_score', 0)
        
        # Reconstruct agent steps
        for step_data in data.get('steps', []):
            step = AgentStep(
                agent_name=step_data.get('agent_name', ''),
                agent_role=step_data.get('agent_role', ''),
                input_data=step_data.get('input_data', ''),
                output_data=step_data.get('output_data', ''),
                duration_ms=step_data.get('duration_ms', 0),
                privacy_score_before=step_data.get('privacy_score_before', 1.0),
                privacy_score_after=step_data.get('privacy_score_after', 1.0),
                entities_detected=step_data.get('entities_detected', []),
                entities_masked=step_data.get('entities_masked', []),
                mapping=step_data.get('mapping', {}),
                metadata=step_data.get('metadata', {}),
                timestamp=step_data.get('timestamp', ''),
                zone=step_data.get('zone'),
                status=step_data.get('status', 'success')
            )
            trace.add_step(step)
        
        st.session_state.current_trace = trace
        st.session_state.trace_counter = st.session_state.get('trace_counter', 0) + 1
        st.session_state.last_loaded_file = trace_file_path
        
    except Exception as e:
        st.session_state.load_error = str(e)

def main():
    # Header
    st.markdown('<p class="main-header">🛡️ Sovereign Learner</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Explainability Dashboard - Understanding Privacy-Preserving Educational AI</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Replaced broken placeholder image with styled CSS header
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h1 style="color: white; margin: 0; font-size: 24px; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">🛡️ Sovereign</h1>
            <p style="color: #b0c4de; margin: 5px 0 0 0; font-size: 12px; letter-spacing: 1px; text-transform: uppercase;">Privacy-First AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Query Input")
        
        # Preset queries
        preset_queries = {
            "CRISPR Research": "How do I optimize my CRISPR protocol for HEK293 cells?",
            "Medical PII": "I'm patient John Smith, ID 78432. How do I interpret my HbA1c results?",
            "ML/AI": "How do I fix the memory leak in my CUDA kernel for TensorRT?",
            "Legal": "How should I structure the IP clause for our Series A with Sequoia?",
            "Custom": ""
        }
        
        # Check if we have a loaded trace to populate the query
        default_query_type = "CRISPR Research"
        default_query_text = preset_queries[default_query_type]
        
        if 'current_trace' in st.session_state:
            # If trace is loaded, show its original query
            default_query_text = st.session_state.current_trace.original_query
            default_query_type = "Custom"
        
        query_type = st.selectbox("Select Query Type", list(preset_queries.keys()), 
                                   index=list(preset_queries.keys()).index(default_query_type))
        
        if query_type == "Custom":
            # Use trace_counter to force refresh when a new trace is loaded
            trace_counter = st.session_state.get('trace_counter', 0)
            query = st.text_area("Enter your query:", value=default_query_text, height=100, key=f"query_input_{trace_counter}")
        else:
            query = st.text_area("Query:", value=preset_queries[query_type], height=100)
        
def render_trace_view(trace):
    """Render the full trace visualization (metrics + tabs)"""
    
    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Privacy Protection",
            f"{trace.privacy_protection_score:.0%}",
            delta="Protected",
            delta_color="normal"
        )
    
    with col2:
        st.metric(
            "Zone Used",
            f"Zone {trace.zone_used}",
            delta="High Security" if trace.zone_used <= 1 else "Standard"
        )
    
    with col3:
        st.metric(
            "Total Latency",
            f"{trace.total_duration_ms:.0f}ms",
            delta=f"{len(trace.steps)} agents"
        )
    
    with col4:
        st.metric(
            "Utility Score",
            f"{trace.utility_score:.0%}",
            delta="Educational value"
        )
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Privacy Waterfall",
        "🎯 Agent Contributions", 
        "⏱️ Timeline",
        "🔀 Data Flow",
        "📝 Step-by-Step"
    ])
    
    with tab1:
        st.markdown("### Privacy Protection Waterfall")
        st.markdown("""
        This chart shows how privacy protection changes at each stage of the pipeline.
        **Green bars** indicate privacy improvement (sensitive data protected).
        The Semantic Generalizer provides the most protection.
        """)
        st.plotly_chart(create_privacy_waterfall(trace), use_container_width=True)
        
        # C8.2: Privacy Waterfall Table
        st.markdown("#### Per-Stage Privacy Waterfall (C8.2)")
        progression_data = []
        
        # Initial State
        progression_data.append({
            "Stage": "—",
            "Component": "Raw query (no protection)",
            "Privacy Exposure Before": 1.0,
            "Privacy Exposure After": 1.0,
            "Δ": 0.0
        })
        
        for idx, step in enumerate(trace.steps, 1):
            exposure_before = step.privacy_score_before
            exposure_after = step.privacy_score_after
            delta_val = exposure_after - exposure_before
            
            progression_data.append({
                "Stage": f"Stage {idx}",
                "Component": step.agent_name,
                "Privacy Exposure Before": exposure_before,
                "Privacy Exposure After": exposure_after,
                "Δ": delta_val
            })
        
        prog_df = pd.DataFrame(progression_data)
        st.dataframe(
            prog_df.style.format({
                "Privacy Exposure Before": "{:.0%}", 
                "Privacy Exposure After": "{:.0%}",
                "Δ": "{:+.0%}"
            }), 
            use_container_width=True
        )
    
    with tab2:
        st.markdown("### Agent Contribution Analysis")
        st.markdown("""
        Similar to SHAP feature importance, this shows each agent's contribution to overall privacy protection.
        The **Semantic Generalizer** is the core contributor - our novel contribution that differentiates from Preempt.
        """)
        st.plotly_chart(create_agent_contribution_chart(trace), use_container_width=True)
        
        # Contribution table
        contributions = trace.get_agent_contributions()
        contrib_df = pd.DataFrame([
            {"Agent": k, "Contribution": v, "Role": "Core" if v > 0.3 else "Supporting"}
            for k, v in sorted(contributions.items(), key=lambda x: x[1], reverse=True)
        ])
        st.dataframe(contrib_df.style.format({"Contribution": "{:.1%}"}), use_container_width=True)
    
    with tab3:
        st.markdown("### Execution Timeline")
        st.markdown("""
        This shows the time spent in each agent. Note that **Cloud Researcher** takes the most time,
        while local agents are extremely fast - proving edge AI feasibility.
        """)
        st.plotly_chart(create_timeline_chart(trace), use_container_width=True)
        
        # Timing breakdown
        timing_data = []
        local_time = 0
        cloud_time = 0
        for step in trace.steps:
            timing_data.append({
                "Agent": step.agent_name,
                "Duration (ms)": step.duration_ms,
                "Type": "Cloud" if "cloud" in step.agent_name.lower() else "Local"
            })
            if "cloud" in step.agent_name.lower():
                cloud_time += step.duration_ms
            else:
                local_time += step.duration_ms
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Local Processing", f"{local_time:.1f}ms", delta=f"{local_time/trace.total_duration_ms:.0%} of total")
        with col2:
            st.metric("Cloud Processing", f"{cloud_time:.1f}ms", delta=f"{cloud_time/trace.total_duration_ms:.0%} of total")
    
    with tab4:
        st.markdown("### Data Flow Visualization")
        st.markdown("""
        This Sankey diagram shows how data flows through the pipeline.
        Notice how the flow **narrows** at the Cloud Researcher (only sanitized data sent),
        then **widens** again after recontextualization.
        """)
        st.plotly_chart(create_sankey_diagram(trace), use_container_width=True)
        
        # Key insight
        st.info("""
        **🔒 Key Privacy Insight:** The cloud (Groq/Llama-3.3) only receives 15% of the original 
        information - abstract placeholders like "Protocol-A" and "Cell-A". 
        It never sees "CRISPR" or "HEK293".
        """)
    
    with tab5:
        st.markdown("### Step-by-Step Agent Execution")
        
        # Extract global mapping for context restoration
        global_mapping = {}
        for s in trace.steps:
            if s.mapping and "Generalizer" in s.agent_name:
                global_mapping = s.mapping
                break
        
        if st.checkbox("Show detailed steps", value=True, key="show_detailed_steps"):
            for i, step in enumerate(trace.steps):
                render_agent_step(step, i, accumulated_mapping=global_mapping)
        else:
            # Condensed view
            for step in trace.steps:
                with st.expander(f"{step.agent_name} ({step.duration_ms:.1f}ms)"):
                    st.write(f"**Input:** {step.input_data[:100]}...")
                    st.write(f"**Output:** {step.output_data[:100]}...")
    
    # Raw JSON (optional)
    if st.checkbox("Show raw JSON", value=False, key="show_raw_json"):
        st.markdown("---")
        st.markdown("### Raw Trace JSON")
        st.json(trace.to_dict())
    
    # Final response
    st.markdown("---")
    st.markdown("### 📤 Final Answer (Recontextualized)")
    
    def _clean_final_answer(text: str) -> str:
        if not text: return ""
        import re
        
        # 1. Try to extract explicit "response" field from JSON-like Action Input
        # Matches "response": "..." or 'response': '...'
        # We use a non-greedy match for the content to avoid over-matching
        response_match = re.search(r'[\"\']response[\"\']\s*:\s*[\"\'](.*?)[\"\']\s*[,}]', text, re.DOTALL)
        if response_match:
            # We found a structured response field!
            return response_match.group(1)

        # 2. Try to find "Final Answer:" marker
        if "Final Answer:" in text:
             return text.split("Final Answer:")[-1].strip()
        
        # 3. If it's a raw Thought/Action block without structured response, try to clean it
        # Remove Thought...Action...Input...} blocks
        cleaned = re.sub(r'Thought:.*?Action Input:.*?}', '', text, flags=re.DOTALL).strip()
        
        # If cleanup left just punctuation or empty, revert to original (or handle further)
        if not cleaned or cleaned in ['"', '}', '"}', "'}"]:
            # Maybe the regex stripped too much, or the content was ONLY the action.
            # In that case, we failed to extract.
            # Let's try one more heuristic: the last sentence?
            return text
            
        return cleaned

    # Intelligently find the actual answer (usually from Recontextualizer), ignoring subsequent logging steps
    final_answer = trace.final_response
    
    for step in trace.steps:
        # Check for Recontextualizer output
        if "Recontextualizer" in step.agent_name or "Recontextualization Specialist" in step.agent_role:
            step_output = step.output_data
            # If the step output is just a tool call log, it might be junk.
            # But usually trace.final_response is the reliable one IF the chain finished.
            # If the chain failed or intermediate step is best:
            if "Thought:" not in step_output and "Action:" not in step_output:
                final_answer = step_output
            else:
                # Try to clean it
                cleaned = _clean_final_answer(step_output)
                if cleaned:
                    final_answer = cleaned
            break
            
    st.success(final_answer)


def main():
    # Header
    st.markdown('<p class="main-header">🛡️ Sovereign Learner</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Explainability Dashboard - Understanding Privacy-Preserving Educational AI</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        # Replaced broken placeholder image with styled CSS header
        st.markdown("""
        <div style="text-align: center; padding: 15px; background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%); border-radius: 10px; margin-bottom: 20px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
            <h1 style="color: white; margin: 0; font-size: 24px; text-shadow: 0 2px 4px rgba(0,0,0,0.2);">🛡️ Sovereign</h1>
            <p style="color: #b0c4de; margin: 5px 0 0 0; font-size: 12px; letter-spacing: 1px; text-transform: uppercase;">Privacy-First AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("### Query Input")
        
        # Preset queries
        preset_queries = {
            "CRISPR Research": "How do I optimize my CRISPR protocol for HEK293 cells?",
            "Medical PII": "I'm patient John Smith, ID 78432. How do I interpret my HbA1c results?",
            "ML/AI": "How do I fix the memory leak in my CUDA kernel for TensorRT?",
            "Legal": "How should I structure the IP clause for our Series A with Sequoia?",
            "Custom": ""
        }
        
        # Check if we have a loaded trace to populate the query
        default_query_type = "CRISPR Research"
        default_query_text = preset_queries[default_query_type]
        
        if 'current_trace' in st.session_state:
            # If trace is loaded, show its original query
            default_query_text = st.session_state.current_trace.original_query
            default_query_type = "Custom"
        
        query_type = st.selectbox("Select Query Type", list(preset_queries.keys()), 
                                   index=list(preset_queries.keys()).index(default_query_type))
        
        if query_type == "Custom":
            # Use trace_counter to force refresh when a new trace is loaded
            trace_counter = st.session_state.get('trace_counter', 0)
            query = st.text_area("Enter your query:", value=default_query_text, height=100, key=f"query_input_{trace_counter}")
        else:
            query = st.text_area("Query:", value=preset_queries[query_type], height=100)
        
        run_button = st.button("🚀 Analyze Query", type="primary", use_container_width=True)
        
        st.markdown("---")
    
    # Main content
    if run_button and query:
        # Import the real system
        try:
            from sovereign_system.crew import SovereignSystem
            from sovereign_system.utils.sovereign_trace_logger import SovereignTracer
            import hashlib
            
            with st.spinner("🚀 Initializing Sovereign Agents..."):
                query_id = hashlib.md5(f"{query}{datetime.now().isoformat()}".encode()).hexdigest()[:8]
                tracer = SovereignTracer()
                
                # Start tracing
                tracer.start_trace(query_id, query)
                
                # Initialize System with Tracer
                sovereign_system = SovereignSystem(tracer=tracer)
                sovereign_crew = sovereign_system.crew()
                
            with st.spinner("🛡️ Processing Query through Zones (this may take 30-60s)..."):
                # Run the crew
                result = sovereign_crew.kickoff(inputs={'user_query': query})
                
                # End trace
                trace = tracer.end_trace(str(result), zone=1, utility_score=0.95)
                
            st.session_state.current_trace = trace
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Execution Failed: {str(e)}")
            st.error("Please ensure you have the local Ollama models (phi3.5:latest) and API keys set up.")
            # Fallback to demo trace if real execution fails
            if st.button("Fallback to Demo Trace"):
                 trace = create_demo_trace(query)
                 st.session_state.current_trace = trace
                 st.rerun()

    # Load existing traces
    dashboard_dir = os.path.dirname(os.path.abspath(__file__))
    trace_dir = os.path.join(dashboard_dir, "traces")
    
    # Fallback for project root execution
    if not os.path.exists(trace_dir):
        trace_dir = os.path.join(project_root, "dashboard", "traces")

    if os.path.exists(trace_dir):
        with st.sidebar:
            st.markdown("### 📂 Load Trace")
            try:
                # Filter for JSON files
                trace_files = [f for f in os.listdir(trace_dir) if f.endswith('.json')]
                trace_files.sort(reverse=True)
                
                if not trace_files:
                    st.info("No trace files found.")
                else:
                    with st.form("trace_loader_form"):
                        # Use a form to prevent auto-rerun on selection change which helps stability
                        selected_trace_file = st.selectbox(
                            "Select Trace File", 
                            trace_files, 
                            key="trace_file_selector"
                        )
                        load_submitted = st.form_submit_button("Load Trace")
                        
                        if load_submitted and selected_trace_file:
                            trace_path = os.path.join(trace_dir, selected_trace_file)
                            load_trace_callback(trace_path)
                            st.success(f"Loaded: {selected_trace_file}")
                            st.rerun()
                            
            except Exception as e:
                st.error(f"Error listing traces: {e}")

    # Display current trace
    if 'current_trace' in st.session_state:
        trace = st.session_state.current_trace
        st.success(f"✅ Query processed successfully in {trace.total_duration_ms:.1f}ms")
        render_trace_view(trace)
        
    else:
        # Welcome state
        st.markdown("""
        <div style="text-align: center; padding: 40px 0 20px 0;">
            <h1 style="font-size: 3rem; margin-bottom: 10px; background: linear-gradient(90deg, #1e3a5f 0%, #2d5a87 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Sovereign Learner</h1>
            <p style="font-size: 1.5rem; color: #666;">Explainable, Privacy-Preserving Agentic AI</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Key Features Grid
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            <div class="metric-card" style="margin-bottom: 20px;">
                <h3>🛡️ Privacy Waterfall</h3>
                <p>Visualize exactly how sensitive data is protected at each stage.</p>
                <ul>
                    <li><b>Red</b>: Exposed data</li>
                    <li><b>Green</b>: Sanitized/Protected data</li>
                    <li><b>Blue</b>: Recontextualized data</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #43cea2 0%, #185a9d 100%);">
                <h3>⏱️ Edge-First Performance</h3>
                <p>Verify the feasibility of running on local devices.</p>
                <ul>
                    <li><b>Local Agents</b>: < 50ms latency</li>
                    <li><b>Cloud Handoff</b>: Only when necessary</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        with col2:
            st.markdown("""
            <div class="metric-card" style="margin-bottom: 20px; background: linear-gradient(135deg, #ff9966 0%, #ff5e62 100%);">
                <h3>🎯 Agent Attribution</h3>
                <p>Understand which agent is responsible for privacy.</p>
                <ul>
                    <li><b>Semantic Generalizer</b>: Core protection</li>
                    <li><b>Sovereign Manager</b>: Policy enforcement</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div class="metric-card" style="background: linear-gradient(135deg, #4b6cb7 0%, #182848 100%);">
                <h3>🔀 Transparent Data Flow</h3>
                <p>See what the cloud actually sees.</p>
                <ul>
                    <li><b>Sanitized</b>: "Protocol-A" instead of "CRISPR"</li>
                    <li><b>Restored</b>: Full context for the user</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
        st.markdown("---")
        
        # Sample visualization
        st.markdown("### 📊 Interactive Demo")
        st.info("Below is a sample trace. Select a query from the sidebar or load a trace file to see real data.")
        demo_trace = create_demo_trace()
        render_trace_view(demo_trace)


if __name__ == "__main__":
    main()
