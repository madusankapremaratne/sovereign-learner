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
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from core system source of truth
from src.sovereign_system.utils.sovereign_trace_logger import SovereignTrace, SovereignTracer, create_demo_trace, AgentStep

# Page config
st.set_page_config(
    page_title="Sovereign Learner - Explainability Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    prev_exposure = 1.0
    
    for step in trace.steps:
        x_data.append(step.agent_name)
        
        current_exposure = step.privacy_score_after
        delta = current_exposure - prev_exposure
        
        # For Bar chart: 
        # If decreasing (delta < 0): Base = Prev, Y = Delta (negative)
        # If increasing (delta > 0): Base = Prev, Y = Delta (positive)
        base_data.append(prev_exposure if delta > 0 else prev_exposure + delta)
        # Actually go.Bar draws from 'base' up to 'base + y'.
        # If y is negative, it draws down? Plotly handles it.
        # Let's stick to: Base is always the bottom of the bar?
        # No, 'base' is the reference line.
        # If I want to draw from 1.0 down to 0.1:
        # Base = 0.1, Y = 0.9? Or Base=1.0, Y=-0.9?
        # Usually Base=1.0, Y=-0.9 works.
        
        base_data.append(prev_exposure)
        y_data.append(delta)
        
        # Color Logic
        if delta < -0.01:
             colors.append("#00C853") # Green (Sanitization)
             text_data.append(f"<b>{delta:+.0%}</b><br>Sanitized")
        elif delta > 0.01:
             if "Recontextualizer" in step.agent_name:
                 colors.append("#448AFF") # Blue (Restored)
                 text_data.append(f"<b>{delta:+.0%}</b><br>Restored")
             else:
                 colors.append("#FF5252") # Red (Leak)
                 text_data.append(f"<b>{delta:+.0%}</b><br>Risk")
        else:
             colors.append("rgba(0,0,0,0)") # Invisible/Grey
             text_data.append("")
             
        prev_exposure = current_exposure

    # Final Bar
    x_data.append("Final")
    y_data.append(prev_exposure)
    base_data.append(0)
    code = "#448AFF" if prev_exposure > 0.8 else "#00C853"
    colors.append(code)
    text_data.append(f"<b>{prev_exposure:.0%}</b><br>Final")
    
    # Create Figure
    fig = go.Figure(go.Bar(
        x=x_data,
        y=y_data,
        base=base_data,
        marker_color=colors,
        text=text_data,
        textposition="outside",
        textfont=dict(size=11)
    ))

    # Add connector lines (simulation)
    # We can add a line shape for each step
    shapes = []
    
    # Safe Zone
    shapes.append(dict(
        type="rect",
        xref="paper", yref="y",
        x0=0, x1=1,
        y0=-0.05, y1=0.2,
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


def render_agent_step(step: AgentStep, index: int):
    """Render a single agent step with details"""
    
    # Determine if local or cloud
    is_cloud = "cloud" in step.agent_name.lower()
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
    
    with st.container():
        st.markdown(f"""
        <div class="agent-box {box_class}">
            <h4>{icon} Step {index + 1}: {step.agent_name}</h4>
            <p><em>{step.agent_role}</em></p>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            st.markdown("**Input:**")
            st.code(step.input_data[:200] + "..." if len(step.input_data) > 200 else step.input_data)
        
        with col2:
            st.markdown("**Output:**")
            st.code(step.output_data[:200] + "..." if len(step.output_data) > 200 else step.output_data)
        
        with col3:
            st.metric("Duration", f"{step.duration_ms:.1f}ms")
            st.markdown(f"<span class='{privacy_class}'>{privacy_indicator}</span>", unsafe_allow_html=True)
        
        # Show mapping if present
        if step.mapping:
            with st.expander("🔀 Mapping Table"):
                mapping_df = pd.DataFrame([
                    {"Placeholder": k, "Original": v} for k, v in step.mapping.items()
                ])
                st.table(mapping_df)
        
        # Show metadata if present
        if step.metadata:
            with st.expander("📋 Metadata"):
                st.json(step.metadata)
        
        st.markdown("---")


def main():
    # Header
    st.markdown('<p class="main-header">🛡️ Sovereign Learner</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Explainability Dashboard - Understanding Privacy-Preserving Educational AI</p>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/200x80?text=Sovereign+Learner", width=200)
        st.markdown("### Query Input")
        
        # Preset queries
        preset_queries = {
            "CRISPR Research": "How do I optimize my CRISPR protocol for HEK293 cells?",
            "Medical PII": "I'm patient John Smith, ID 78432. How do I interpret my HbA1c results?",
            "ML/AI": "How do I fix the memory leak in my CUDA kernel for TensorRT?",
            "Legal": "How should I structure the IP clause for our Series A with Sequoia?",
            "Custom": ""
        }
        
        query_type = st.selectbox("Select Query Type", list(preset_queries.keys()))
        
        if query_type == "Custom":
            query = st.text_area("Enter your query:", height=100)
        else:
            query = st.text_area("Query:", value=preset_queries[query_type], height=100)
        
        run_button = st.button("🚀 Analyze Query", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.markdown("### Configuration")
        show_detailed = st.checkbox("Show detailed steps", value=True)
        show_raw_json = st.checkbox("Show raw JSON", value=False)
    
    # Main content
    if run_button and query:
        with st.spinner("Processing query through Sovereign Learner pipeline..."):
            # Create demo trace (in production, this would call the actual pipeline)
            trace = create_demo_trace(query)
            time.sleep(0.5)  # Simulate processing
        st.session_state.current_trace = trace
        st.rerun()

    # Load existing traces
    trace_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "traces")
    if os.path.exists(trace_dir):
        with st.sidebar:
            st.markdown("### 📂 Load Trace")
            trace_files = [f for f in os.listdir(trace_dir) if f.endswith('.json')]
            trace_files.sort(reverse=True)
            
            selected_trace_file = st.selectbox("Select Trace", ["Current Run"] + trace_files)
            
            if selected_trace_file != "Current Run":
                 if st.button("Load Trace"):
                    try:
                        with open(os.path.join(trace_dir, selected_trace_file), 'r') as f:
                            data = json.load(f)
                            # Reconstruct trace object (simplified)
                            # Ideally would use from_dict but for now manual or just use dict if view supports it
                            # But our view functions expect SovereignTrace object. 
                            # Let's quick-fix by just creating a dummy object and filling it
                            trace = SovereignTrace(
                                query_id=data.get('query_id', 'loaded'),
                                original_query=data.get('original_query', '')
                            )
                            trace.final_response = data.get('final_response', '')
                            trace.total_duration_ms = data.get('total_duration_ms', 0)
                            trace.zone_used = data.get('zone_used', 1)
                            trace.privacy_protection_score = data.get('privacy_protection_score', 0)
                            trace.utility_score = data.get('utility_score', 0)
                            
                            for s in data.get('steps', []):
                                trace.add_step(AgentStep(**s))
                                
                            st.session_state.current_trace = trace
                            st.success(f"Loaded {selected_trace_file}")
                            st.rerun()
                    except Exception as e:
                        st.error(f"Error loading trace: {e}")

    # Display current trace
    if 'current_trace' in st.session_state:
        trace = st.session_state.current_trace
        st.success(f"✅ Query processed successfully in {trace.total_duration_ms:.1f}ms")
        
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
            
            # Privacy score progression
            st.markdown("#### Privacy Score Progression")
            progression_data = []
            for step in trace.steps:
                progression_data.append({
                    "Agent": step.agent_name,
                    "Before": step.privacy_score_before,
                    "After": step.privacy_score_after
                })
            
            prog_df = pd.DataFrame(progression_data)
            st.dataframe(prog_df.style.format({"Before": "{:.0%}", "After": "{:.0%}"}), use_container_width=True)
        
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
            **🔒 Key Privacy Insight:** The cloud (Gemini) only receives 15% of the original 
            information - abstract placeholders like "Protocol-A" and "Cell-A". 
            It never sees "CRISPR" or "HEK293".
            """)
        
        with tab5:
            st.markdown("### Step-by-Step Agent Execution")
            
            if show_detailed:
                for i, step in enumerate(trace.steps):
                    render_agent_step(step, i)
            else:
                # Condensed view
                for step in trace.steps:
                    with st.expander(f"{step.agent_name} ({step.duration_ms:.1f}ms)"):
                        st.write(f"**Input:** {step.input_data[:100]}...")
                        st.write(f"**Output:** {step.output_data[:100]}...")
        
        # Raw JSON (optional)
        if show_raw_json:
            st.markdown("---")
            st.markdown("### Raw Trace JSON")
            st.json(trace.to_dict())
        
        # Final response
        st.markdown("---")
        st.markdown("### 📤 Final Response to Learner")
        st.success(trace.final_response)
        
    else:
        # Welcome state
        st.markdown("""
        ## Welcome to the Sovereign Learner Explainability Dashboard
        
        This dashboard demonstrates how queries navigate through the privacy-preserving educational AI pipeline.
        
        ### How to Use
        1. Select a query type from the sidebar (or enter a custom query)
        2. Click **Analyze Query**
        3. Explore the visualizations to understand how privacy is protected
        
        ### Key Features
        - **Privacy Waterfall**: See how sensitive information is progressively protected
        - **Agent Contributions**: Understand which agents contribute most to privacy
        - **Timeline**: View execution time breakdown (proving edge AI feasibility)
        - **Data Flow**: Visualize how data moves through the pipeline
        
        ### For Prof. Daswin & Dr. Nishan
        This dashboard provides **SHAP-like explainability** for agentic AI systems,
        showing how each agent contributes to the overall privacy protection goal.
        """)
        
        # Sample visualization
        st.markdown("### Sample: Agent Contribution (Click 'Analyze Query' for live data)")
        demo_trace = create_demo_trace()
        st.plotly_chart(create_agent_contribution_chart(demo_trace), use_container_width=True)


if __name__ == "__main__":
    main()
