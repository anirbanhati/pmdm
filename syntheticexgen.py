import random
import json
import re
from typing import List, Dict, Tuple, Set
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class AttributeConfig:
    """Configuration for an attribute in the rule system"""
    name: str  # Display name (e.g., "Calc_Brand")
    variable: str  # Variable name (e.g., "calc_brand")
    has_language: bool = False
    suppress_values: List[str] = None
    
    def __post_init__(self):
        if self.suppress_values is None:
            self.suppress_values = []

class RuleGenerator:
    """Generates synthetic business rule expressions with reassignment tracking"""
    
    def __init__(self):
        # Define all known attributes based on your examples
        self.attributes = {
            "calc_brand": AttributeConfig("Calc_Brand", "calc_brand"),
            "type_range": AttributeConfig("Type_Range", "type_range", has_language=True),
            "material_type": AttributeConfig("Material_type", "material_type", 
                                            suppress_values=[" Wooden", " Metal", " Glass"]),
            "vdesc_colour": AttributeConfig("Vdesc_Colour", "vdesc_colour", 
                                           has_language=True),
            "use_foldable": AttributeConfig("Use_Foldable", "use_foldable",
                                           suppress_values=[" Non-foldable", " Fixed"]),
            "number_of_seats": AttributeConfig("Number_of_seats", "number_of_seats"),
            "tech_extendable": AttributeConfig("Tech_Extendable", "tech_extendable",
                                              suppress_values=[" Non extendable", " Fixed", 
                                                             " Non-extendable"]),
            "vdesc_product_shape": AttributeConfig("Vdesc_Product shape", "vdesc_product_shape"),
            "core_product_type": AttributeConfig("Core_Product type", "core_product_type"),
            "key_feature": AttributeConfig("Key_Feature", "key_feature", has_language=True),
            # Extended attributes for variety
            "assembly_required": AttributeConfig("Assembly_Required", "assembly_required",
                                                suppress_values=[" No", " Not required"]),
            "weight_capacity": AttributeConfig("Weight_Capacity", "weight_capacity",
                                              suppress_values=[" N/A", " Not applicable"]),
            "warranty_period": AttributeConfig("Warranty_Period", "warranty_period"),
            "frame_material": AttributeConfig("Frame_Material", "frame_material",
                                             suppress_values=[" N/A", " Not specified"]),
            "cushion_type": AttributeConfig("Cushion_Type", "cushion_type",
                                           suppress_values=[" None", " Not applicable"]),
            "style": AttributeConfig("Style", "style", has_language=True),
            "room_type": AttributeConfig("Room_Type", "room_type"),
        }
        
        self.language_codes = ['"en_GB"', '"en_US"', '"fr_FR"', '"de_DE"', '"es_ES"']
        
    def generate_attribute_block(self, attr_key: str, use_language: bool = None) -> List[str]:
        """
        Generates the initial definition block for an attribute.
        Returns list of lines for this attribute.
        """
        attr = self.attributes[attr_key]
        
        # Decide on language usage
        if use_language is None:
            use_language = attr.has_language and random.random() > 0.5
        
        # Build the validation line
        if use_language:
            lang = random.choice(self.language_codes)
            validate_line = f'{attr.variable} := IIF[ValidateEmptyAttributes["{attr.name}",IGNORESOURCEFLAG,{lang}],""'
            value_line = f'Concat[" ", AttributeValue["{attr.name}",{lang}]]'
        else:
            validate_line = f'{attr.variable} := IIF[ValidateEmptyAttributes["{attr.name}",IGNORESOURCEFLAG],""'
            value_line = f'Concat[" ", AttributeValue["{attr.name}"]]'
        
        return [validate_line + ",", value_line]
    
    def generate_suppression(self, target_var: str, condition_var: str) -> str:
        """Generate a suppression rule between two variables"""
        condition_attr = self.attributes.get(condition_var)
        target_attr = self.attributes.get(target_var)
        
        if condition_attr and condition_attr.suppress_values:
            suppress_val = random.choice(condition_attr.suppress_values)
        else:
            # Generate a plausible suppression value
            suppress_val = f" {random.choice(['N/A', 'None', 'Not applicable', 'Test', 'Sample'])}"
        
        return f'{target_var} :=IIF[{condition_var}="{suppress_val}","",{target_var}];'
    
    def generate_complete_rule(self, 
                               num_attributes: int = None,
                               num_suppressions: int = None,
                               complexity: str = "random") -> Tuple[str, Dict]:
        """
        Generate a complete rule expression and its reassignment JSON.
        
        Args:
            num_attributes: Number of attributes to include (random if None)
            num_suppressions: Number of suppression rules (random if None)
            complexity: "simple", "medium", "complex", or "random"
        
        Returns:
            (rule_text, json_output)
        """
        # Set complexity parameters
        if complexity == "simple":
            num_attributes = num_attributes or random.randint(3, 5)
            num_suppressions = num_suppressions or random.randint(0, 2)
        elif complexity == "medium":
            num_attributes = num_attributes or random.randint(5, 8)
            num_suppressions = num_suppressions or random.randint(2, 4)
        elif complexity == "complex":
            num_attributes = num_attributes or random.randint(8, 12)
            num_suppressions = num_suppressions or random.randint(4, 8)
        else:  # random
            num_attributes = num_attributes or random.randint(3, 12)
            num_suppressions = num_suppressions or random.randint(0, 8)
        
        # Select random attributes
        attr_keys = random.sample(list(self.attributes.keys()), 
                                 min(num_attributes, len(self.attributes)))
        
        # Track variable definitions and reassignments
        variable_lines = defaultdict(list)  # variable -> list of definition lines
        all_lines = []  # All lines in order
        reassignment_map = defaultdict(list)  # variable -> list of reassignment lines
        
        # Generate initial definitions for all attributes
        for attr_key in attr_keys:
            block_lines = self.generate_attribute_block(attr_key)
            var = self.attributes[attr_key].variable
            
            # First line gets a comma
            variable_lines[var].append(block_lines[0])
            all_lines.append(block_lines[0])
            
            # Second line (and any subsequent from block)
            for line in block_lines[1:]:
                variable_lines[var].append(line)
                all_lines.append(line)
        
        # Generate cross-variable suppressions
        possible_suppression_pairs = []
        for target in attr_keys:
            target_var = self.attributes[target].variable
            for condition in attr_keys:
                if condition != target:
                    condition_var = self.attributes[condition].variable
                    if self.attributes[condition].suppress_values:
                        possible_suppression_pairs.append((target_var, condition_var))
        
        # Select suppression pairs
        if possible_suppression_pairs:
            num_suppressions = min(num_suppressions, len(possible_suppression_pairs))
            selected_suppressions = random.sample(possible_suppression_pairs, num_suppressions)
            
            for target_var, condition_var in selected_suppressions:
                suppression_line = self.generate_suppression(target_var, condition_var)
                all_lines.append(suppression_line)
                reassignment_map[target_var].append(suppression_line)
        
        # Also add self-suppressions (like vdesc_colour for Wooden material)
        for attr_key in attr_keys:
            attr = self.attributes[attr_key]
            if attr.suppress_values and random.random() > 0.7:
                # Self-suppression based on another variable's value
                other_attrs = [a for a in attr_keys if a != attr_key]
                if other_attrs:
                    condition_key = random.choice(other_attrs)
                    condition_var = self.attributes[condition_key].variable
                    suppression_line = self.generate_suppression(attr.variable, condition_var)
                    if suppression_line not in all_lines:
                        all_lines.append(suppression_line)
                        reassignment_map[attr.variable].append(suppression_line)
        
        # Generate CONCAT line
        concat_vars = [self.attributes[k].variable for k in attr_keys]
        concat_line = f'Concat[{", ".join(concat_vars)}]'
        all_lines.append(concat_line)
        
        # Build JSON output - ONLY include variables that have reassignments
        json_output = {}
        for var in attr_keys:
            var_name = self.attributes[var].variable
            if var_name in reassignment_map and reassignment_map[var_name]:
                # Include original definition lines plus reassignments plus concat
                entry_lines = variable_lines[var_name].copy()
                entry_lines.extend(reassignment_map[var_name])
                entry_lines.append(concat_line)
                json_output[var_name] = entry_lines
        
        rule_text = "\n".join(all_lines)
        return rule_text, json_output
    
    def generate_dataset(self, 
                        n_examples: int = 500,
                        complexity_distribution: Dict[str, float] = None) -> List[Dict]:
        """
        Generate a dataset of synthetic examples.
        
        Args:
            n_examples: Total number of examples to generate
            complexity_distribution: Dict mapping complexity levels to probabilities
                                    e.g., {"simple": 0.3, "medium": 0.4, "complex": 0.3}
        """
        if complexity_distribution is None:
            complexity_distribution = {
                "simple": 0.3,
                "medium": 0.4,
                "complex": 0.3
            }
        
        examples = []
        complexities = list(complexity_distribution.keys())
        weights = list(complexity_distribution.values())
        
        for i in range(n_examples):
            complexity = random.choices(complexities, weights=weights)[0]
            rule_text, json_output = self.generate_complete_rule(complexity=complexity)
            
            examples.append({
                "input": rule_text,
                "output": json_output
            })
            
            if (i + 1) % 100 == 0:
                print(f"Generated {i + 1}/{n_examples} examples...")
        
        return examples
    
    def validate_example(self, example: Dict) -> bool:
        """
        Validate a generated example for correctness.
        """
        rule_text = example["input"]
        json_output = example["output"]
        
        # Check 1: All variables in JSON should appear multiple times in input
        for var in json_output:
            occurrences = len(re.findall(f'{re.escape(var)} :=', rule_text))
            if occurrences < 2:  # Must have at least one reassignment
                return False
        
        # Check 2: JSON structure matches rule text
        for var, lines in json_output.items():
            for line in lines[:-1]:  # All except last line (concat)
                if line not in rule_text:
                    return False
        
        # Check 3: Concat line should be last in JSON entries
        for var, lines in json_output.items():
            if not lines[-1].startswith("Concat["):
                return False
        
        return True
    
    def deduplicate_examples(self, examples: List[Dict], 
                            similarity_threshold: float = 0.9) -> List[Dict]:
        """
        Remove near-duplicate examples based on structural similarity.
        """
        unique_examples = []
        seen_patterns = []
        
        for example in examples:
            # Extract structural pattern (variable names and suppression patterns)
            pattern = self._extract_pattern(example)
            
            # Check similarity with existing patterns
            is_duplicate = False
            for seen in seen_patterns:
                similarity = self._pattern_similarity(pattern, seen)
                if similarity > similarity_threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_examples.append(example)
                seen_patterns.append(pattern)
        
        return unique_examples
    
    def _extract_pattern(self, example: Dict) -> Tuple:
        """Extract structural pattern from an example"""
        rule_text = example["input"]
        
        # Extract variable names
        variables = tuple(sorted(set(re.findall(r'(\w+) :=', rule_text))))
        
        # Extract suppression count per variable
        suppressions = tuple(sorted(
            (var, rule_text.count(f'{var} :=')) 
            for var in variables
        ))
        
        return (variables, suppressions)
    
    def _pattern_similarity(self, pattern1: Tuple, pattern2: Tuple) -> float:
        """Calculate similarity between two patterns"""
        vars1, supps1 = pattern1
        vars2, supps2 = pattern2
        
        # Variable overlap
        var_overlap = len(set(vars1) & set(vars2)) / max(len(set(vars1) | set(vars2)), 1)
        
        # Suppression pattern similarity
        supp_dict1 = dict(supps1)
        supp_dict2 = dict(supps2)
        
        common_vars = set(supp_dict1.keys()) & set(supp_dict2.keys())
        if common_vars:
            supp_similarity = sum(
                1 for v in common_vars if supp_dict1[v] == supp_dict2[v]
            ) / len(common_vars)
        else:
            supp_similarity = 0
        
        return (var_overlap + supp_similarity) / 2

# Main execution
def generate_500_examples():
    """Generate 500 high-quality synthetic examples"""
    
    print("Initializing rule generator...")
    generator = RuleGenerator()
    
    print("Generating 600 examples (extra for quality filtering)...")
    examples = generator.generate_dataset(
        n_examples=600,
        complexity_distribution={
            "simple": 0.25,   # 25% simple rules
            "medium": 0.45,   # 45% medium complexity
            "complex": 0.30   # 30% complex rules
        }
    )
    
    print("Validating examples...")
    valid_examples = [ex for ex in examples if generator.validate_example(ex)]
    print(f"Valid examples: {len(valid_examples)}/{len(examples)}")
    
    print("Deduplicating...")
    unique_examples = generator.deduplicate_examples(valid_examples, similarity_threshold=0.85)
    print(f"Unique examples: {len(unique_examples)}/{len(valid_examples)}")
    
    # Take exactly 500
    final_examples = unique_examples[:500]
    
    # Save to file
    print("Saving to file...")
    with open('synthetic_business_rules.jsonl', 'w') as f:
        for example in final_examples:
            f.write(json.dumps(example) + '\n')
    
    # Also save as formatted JSON for inspection
    with open('synthetic_business_rules_formatted.json', 'w') as f:
        json.dump(final_examples, f, indent=2)
    
    print(f"Successfully generated {len(final_examples)} examples!")
    
    # Print statistics
    print_statistics(final_examples)
    
    return final_examples

def print_statistics(examples):
    """Print statistics about the generated dataset"""
    total_vars = 0
    total_suppressions = 0
    
    for ex in examples:
        vars_count = len(set(re.findall(r'(\w+) :=', ex["input"])))
        suppressions_count = len(re.findall(r':=IIF\[', ex["input"])) - vars_count
        total_vars += vars_count
        total_suppressions += suppressions_count
    
    avg_vars = total_vars / len(examples)
    avg_suppressions = total_suppressions / len(examples)
    
    print("\n=== Dataset Statistics ===")
    print(f"Total examples: {len(examples)}")
    print(f"Average variables per example: {avg_vars:.1f}")
    print(f"Average suppressions per example: {avg_suppressions:.1f}")
    print(f"Examples with language parameters: {sum(1 for ex in examples if 'en_GB' in ex['input'] or 'en_US' in ex['input'])}")
    
    # Show a sample
    print("\n=== Sample Example ===")
    sample = random.choice(examples)
    print("INPUT:")
    print(sample["input"][:500] + "..." if len(sample["input"]) > 500 else sample["input"])
    print("\nOUTPUT:")
    print(json.dumps(sample["output"], indent=2)[:500])


if __name__ == "__main__":
    examples = generate_500_examples()
    
    # Optional: Display some examples
    print("\n=== First 3 Examples ===")
    for i, ex in enumerate(examples[:3]):
        print(f"\n--- Example {i+1} ---")
        print("Variables tracked for reassignment:", list(ex["output"].keys()))