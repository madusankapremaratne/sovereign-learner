import os

file_path = "experiments/exp02_oulad_hybrid_learning.py"
with open(file_path, "r") as f:
    orig = f.read()

# Shared prefixes
header = orig[:orig.find("@dataclass\nclass StruggleDetectionResult:")]

# Dataclasses and classes
class_str_struggle = orig[orig.find("@dataclass\nclass StruggleDetectionResult:"):orig.find("@dataclass \nclass PortabilityResult:")]
class_str_port = orig[orig.find("@dataclass \nclass PortabilityResult:"):orig.find("class OULADDataLoader:")]
class_str_loader = orig[orig.find("class OULADDataLoader:"):orig.find("class StruggleDetectionExperiment:")]

exp2a_code = orig[orig.find("class StruggleDetectionExperiment:"):orig.find("@dataclass\nclass ComplexQueryResult:")]
# For EXP 2B
exp2b_prefix = orig[orig.find("@dataclass\nclass ComplexQueryResult:"):orig.find("class ComplexQueryExperiment:")]
exp2b_code = orig[orig.find("class ComplexQueryExperiment:"):orig.find("class CompetencyPortabilityExperiment:")]

# For EXP 2C
exp2c_code = orig[orig.find("class CompetencyPortabilityExperiment:"):orig.find("def run_all_experiments(")]


def write_file(filename, content):
    with open(filename, "w") as f:
        f.write(content)

# File 2A 
header_2a = header.replace("Experiment 2: OULAD Hybrid Learning & Struggle Detection", "Experiment 2A: OULAD Passive Struggle Detection")
code_2a = header_2a + "\n" + class_str_struggle + "\n" + class_str_loader + "\n" + exp2a_code + "\n\nif __name__ == '__main__':\n    loader = OULADDataLoader().load_all()\n    exp = StruggleDetectionExperiment(loader.get_student_features())\n    exp.run()"
write_file("experiments/exp02a_passive_struggle.py", code_2a)

# File 2B 
header_2b = header.replace("Experiment 2: OULAD Hybrid Learning & Struggle Detection", "Experiment 2B: OULAD Complex Query Resolution")
code_2b = header_2b + "\n" + exp2b_prefix + "\n" + class_str_loader + "\n" + exp2b_code + "\n\nif __name__ == '__main__':\n    loader = OULADDataLoader().load_all()\n    exp = ComplexQueryExperiment(loader)\n    exp.run()"
write_file("experiments/exp02b_complex_query.py", code_2b)

# File 2C 
header_2c = header.replace("Experiment 2: OULAD Hybrid Learning & Struggle Detection", "Experiment 2C: OULAD Competency Portability")
code_2c = header_2c + "\n" + class_str_port + "\n" + class_str_loader + "\n" + exp2c_code + "\n\nif __name__ == '__main__':\n    loader = OULADDataLoader().load_all()\n    exp = CompetencyPortabilityExperiment(loader)\n    exp.run()"
write_file("experiments/exp02c_competency_transfer.py", code_2c)

print("Split completed successfully.")
