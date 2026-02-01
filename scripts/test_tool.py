from sovereign_system.tools.competency_tools import CompetencyEvidenceTool

tool = CompetencyEvidenceTool()
print("Testing tool...")
result = tool._run(query="Test Query", response="Test Response", zone=1, interaction_type="active")
print(result)
