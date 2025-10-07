#!/usr/bin/env python3
"""
Interactive MER Refinement System

This script provides an interactive console interface to refine a generated MER schema
by allowing users to ask questions and receive AI-powered improvements.
"""

import json
import os
import sys
import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# Add parent directory to path to import llm module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from llm.openai_client import run_model


def load_mer_schema(file_path: str) -> Dict[str, Any]:
    """Load MER schema from JSON file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: Schema file '{file_path}' not found.")
        print("Please run the schema generation pipeline first.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"❌ Error: Invalid JSON in '{file_path}': {e}")
        sys.exit(1)


def save_mer_schema(schema: Dict[str, Any], file_path: str) -> None:
    """Save refined MER schema to JSON file"""
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        print(f"💾 Refined schema saved to: {file_path}")
    except Exception as e:
        print(f"❌ Error saving schema: {e}")


def display_schema_summary(schema: Dict[str, Any]) -> None:
    """Display a summary of the current schema"""
    print("\n" + "="*60)
    print("📊 CURRENT SCHEMA SUMMARY")
    print("="*60)
    
    entities = schema.get('entities', [])
    relationships = schema.get('relationships', [])
    enums = schema.get('enums', [])
    
    print(f"📋 Entities: {len(entities)}")
    for entity in entities:
        name = entity.get('name', 'Unknown')
        attrs = entity.get('attributes', [])
        description = entity.get('description', 'No description')
        print(f"   • {name}: {len(attrs)} attributes")
        print(f"     └─ {description[:80]}{'...' if len(description) > 80 else ''}")
    
    print(f"\n🔗 Relationships: {len(relationships)}")
    for rel in relationships:
        from_entity = rel.get('from_entity', '?')
        to_entity = rel.get('to_entity', '?')
        rel_type = rel.get('type', 'unknown')
        cardinality = rel.get('cardinality', 'unknown')
        print(f"   • {from_entity} -> {to_entity} ({rel_type}, {cardinality})")
    
    if enums:
        print(f"\n📝 Enums: {len(enums)}")
        for enum in enums:
            name = enum.get('name', 'Unknown')
            values = enum.get('values', [])
            print(f"   • {name}: {len(values)} values")
    
    # Show open questions if any
    open_questions = schema.get('meta', {}).get('open_questions', [])
    if open_questions:
        print(f"\n❓ Open Questions: {len(open_questions)}")
        for i, question in enumerate(open_questions[:3], 1):
            print(f"   {i}. {question}")
        if len(open_questions) > 3:
            print(f"   ... and {len(open_questions) - 3} more")
    
    print("="*60)


def extract_questions_from_schema(schema: Dict[str, Any]) -> List[str]:
    """Extract open questions from schema or generate intelligent questions based on schema analysis"""
    
    # First, try to get open questions from the schema
    open_questions = schema.get('meta', {}).get('open_questions', [])
    
    if open_questions:
        print(f"\n🔍 Found {len(open_questions)} open questions from schema generation:")
        for i, question in enumerate(open_questions, 1):
            print(f"   {i}. {question}")
        return open_questions
    
    print("\n🔍 No open questions found in schema. Generating intelligent questions based on schema analysis...")
    
    # Generate intelligent questions based on schema structure
    generated_questions = []
    entities = schema.get('entities', [])
    relationships = schema.get('relationships', [])
    enums = schema.get('enums', [])
    
    # Questions about missing common attributes
    for entity in entities:
        name = entity.get('name', '')
        attrs = entity.get('attributes', [])
        attr_names = [attr.get('name', '') for attr in attrs]
        
        # Check for common missing attributes
        if name.lower() == 'user' and 'created_at' not in attr_names:
            generated_questions.append(f"Should the {name} entity have timestamp fields like created_at and updated_at?")
        
        if name.lower() == 'user' and 'role' not in attr_names and 'status' not in attr_names:
            generated_questions.append(f"Should the {name} entity have a role or status field for access control?")
        
        if name.lower() == 'project' and 'status' not in attr_names:
            generated_questions.append(f"Should the {name} entity have a status field (active, completed, archived)?")
        
        if name.lower() == 'session' and 'created_at' not in attr_names:
            generated_questions.append(f"Should the {name} entity track creation time for security auditing?")
    
    # Questions about potential missing relationships
    entity_names = [e.get('name', '') for e in entities]
    relationship_pairs = set()
    for rel in relationships:
        from_entity = rel.get('from', '')
        to_entity = rel.get('to', '')
        relationship_pairs.add(f"{from_entity}-{to_entity}")
        relationship_pairs.add(f"{to_entity}-{from_entity}")
    
    # Check for Project-Session relationship
    if 'Project' in entity_names and 'Session' in entity_names:
        if 'Project-Session' not in relationship_pairs:
            generated_questions.append("Should there be a relationship between Project and Session (e.g., tracking which project was accessed in each session)?")
    
    # Questions about enums usage
    if enums:
        enum_names = [e.get('name', '') for e in enums]
        if 'UserRole' in enum_names:
            user_attrs = []
            for entity in entities:
                if entity.get('name', '').lower() == 'user':
                    user_attrs = [attr.get('name', '') for attr in entity.get('attributes', [])]
                    break
            if 'role' not in user_attrs:
                generated_questions.append("Should the User entity use the UserRole enum that was defined?")
        
        if 'ProjectPriority' in enum_names:
            project_attrs = []
            for entity in entities:
                if entity.get('name', '').lower() == 'project':
                    project_attrs = [attr.get('name', '') for attr in entity.get('attributes', [])]
                    break
            if 'priority' not in project_attrs:
                generated_questions.append("Should the Project entity use the ProjectPriority enum that was defined?")
    
    # General schema improvement questions
    generated_questions.extend([
        "Are there any business rules or constraints that should be added to ensure data integrity?",
        "What indexes should be created for optimal query performance?",
        "Are there any security considerations for sensitive attributes like passwords or tokens?"
    ])
    
    print(f"📝 Generated {len(generated_questions)} intelligent questions")
    
    return generated_questions


def save_progress_to_markdown(questions_with_status: List[Dict[str, str]], schema: Dict[str, Any], output_file: str = "") -> str:
    """Save progress (answered and pending questions) to markdown file"""
    
    if not output_file:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"questions_progress_{timestamp}.md"
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    answered_count = len([q for q in questions_with_status if q["status"] == "answered"])
    skipped_count = len([q for q in questions_with_status if q["status"] == "skipped"])
    
    markdown_content = f"""# Schema Refinement Progress

**Generated on:** {timestamp}  
**Schema File:** {schema.get('meta', {}).get('source_file', 'mer.json')}  
**Total Questions:** {len(questions_with_status)}  
**Answered:** {answered_count}  
**Pending:** {skipped_count}

## Instructions

This file contains your progress from the interactive refinement session:
- ✅ **Answered questions** - These will be processed by AI
- ⏸️ **Pending questions** - You can fill these in and re-run the process

To continue refinement:
1. Fill in answers for pending questions below
2. Save this file  
3. Run: `uv run python pipeline/interactive_refinement.py --from-markdown {output_file}`

---

"""
    
    # Answered questions first
    if answered_count > 0:
        markdown_content += f"""## ✅ Answered Questions ({answered_count})

These questions have been answered and will be processed by AI:

"""
        
        answered_num = 1
        for item in questions_with_status:
            if item["status"] == "answered":
                markdown_content += f"""### Question {answered_num}

**Q:** {item["question"]}

**Your Answer:**
```
{item["answer"]}
```

---

"""
                answered_num += 1
    
    # Pending questions
    if skipped_count > 0:
        markdown_content += f"""## ⏸️ Pending Questions ({skipped_count})

These questions were skipped. You can fill in answers below:

"""
        
        pending_num = 1
        for item in questions_with_status:
            if item["status"] == "skipped":
                markdown_content += f"""### Pending Question {pending_num}

**Q:** {item["question"]}

**Your Answer:**
```
[Write your answer here or leave blank to skip]
```

---

"""
                pending_num += 1
    
    markdown_content += f"""## Additional Notes

If you have any additional suggestions, comments, or requirements, please add them here:

```
[Write any additional notes here]
```

---

## How to Continue

To process the answered questions:
- Run: `uv run python pipeline/interactive_refinement.py --from-markdown {output_file}`

To continue the interactive session with pending questions:
- Run: `uv run python pipeline/interactive_refinement.py`

"""
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"💾 Progress saved to markdown: {output_file}")
        print(f"📊 Summary: {answered_count} answered, {skipped_count} pending")
        return output_file
    except Exception as e:
        print(f"❌ Error saving progress: {e}")
        return ""


def generate_questions_markdown(questions: List[str], schema: Dict[str, Any], output_file: str = "questions.md") -> str:
    """Generate a markdown file with questions and spaces for answers"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    markdown_content = f"""# Schema Refinement Questions

**Generated on:** {timestamp}  
**Schema File:** {schema.get('meta', {}).get('source_file', 'mer.json')}  
**Total Questions:** {len(questions)}

## Instructions

Please fill in your answers in the spaces provided after each question. You can:
- Write detailed answers for questions you want to address
- Leave blank or write "SKIP" for questions you want to ignore
- Add additional comments or suggestions in the "Additional Notes" section

---

"""
    
    for i, question in enumerate(questions, 1):
        markdown_content += f"""## Question {i}

**Q:** {question}

**Your Answer:**
```
[Write your answer here]
```

---

"""
    
    markdown_content += f"""## Additional Notes

If you have any additional suggestions, comments, or requirements not covered by the questions above, please add them here:

```
[Write any additional notes here]
```

---

## How to Use This File

1. Fill in your answers in the spaces provided above
2. Save this file
3. Run the refinement tool with: `uv run python pipeline/interactive_refinement.py --from-markdown {output_file}`

"""
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        print(f"📝 Questions markdown generated: {output_file}")
        return output_file
    except Exception as e:
        print(f"❌ Error generating markdown: {e}")
        return ""


def parse_markdown_answers(markdown_file: str) -> List[Dict[str, str]]:
    """Parse answers from a markdown file"""
    
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: Markdown file '{markdown_file}' not found.")
        return []
    except Exception as e:
        print(f"❌ Error reading markdown file: {e}")
        return []
    
    answered_questions = []
    
    # Parse questions and answers using regex - handle both formats
    # Format 1: ### Question 1 (from answered section)
    pattern1 = r'### Question (\d+)\s*\n\*\*Q:\*\* (.+?)\n\*\*Your Answer:\*\*\s*\n```\s*\n(.*?)\n```'
    matches1 = re.findall(pattern1, content, re.DOTALL)
    
    # Format 2: ### Pending Question 1 (from pending section)
    pattern2 = r'### Pending Question (\d+)\s*\n\*\*Q:\*\* (.+?)\n\*\*Your Answer:\*\*\s*\n```\s*\n(.*?)\n```'
    matches2 = re.findall(pattern2, content, re.DOTALL)
    
    # Combine all matches
    all_matches = matches1 + matches2
    
    for match in all_matches:
        question_num, question, answer = match
        answer = answer.strip()
        
        # Skip empty answers or placeholder text
        if answer and answer.upper() not in ['SKIP', '[WRITE YOUR ANSWER HERE]', '[WRITE YOUR ANSWER HERE OR LEAVE BLANK TO SKIP]', '']:
            answered_questions.append({
                "question": question.strip(),
                "answer": answer
            })
    
    # Parse additional notes
    notes_pattern = r'## Additional Notes.*?\n```\s*\n(.*?)\n```'
    notes_match = re.search(notes_pattern, content, re.DOTALL)
    
    if notes_match:
        additional_notes = notes_match.group(1).strip()
        if additional_notes and additional_notes.upper() not in ['[WRITE ANY ADDITIONAL NOTES HERE]', '']:
            answered_questions.append({
                "question": "Additional requirements or suggestions from the user",
                "answer": additional_notes
            })
    
    print(f"📊 Parsed {len(answered_questions)} answered questions from markdown")
    
    return answered_questions


def interactive_question_menu(questions: List[str], schema: Dict[str, Any]) -> List[Dict[str, str]]:
    """Interactive menu to go through questions one by one"""
    print(f"\n🎯 Interactive Question Menu")
    print("="*50)
    print("📋 I'll show you each question. You can:")
    print("   • (A)nswer it - provide your response")
    print("   • (S)kip it - add to pending questions")
    print("   • (Q)uit - stop the refinement process")
    print("="*50)
    print("📝 Note: All questions (answered and skipped) will be saved to a markdown file")
    
    answered_questions = []
    all_questions_with_status = []  # Track all questions with their status
    
    for i, question in enumerate(questions, 1):
        print(f"\n❓ Question {i}/{len(questions)}:")
        print(f"   {question}")
        
        question_handled = False
        while True:
            try:
                choice = input(f"\n   What would you like to do? (A)nswer / (S)kip / (Q)uit: ").upper().strip()
                
                if choice in ['Q', 'QUIT']:
                    print("👋 Exiting refinement process...")
                    # Generate markdown with current progress before exiting
                    save_progress_to_markdown(all_questions_with_status, schema)
                    return answered_questions
                
                elif choice in ['S', 'SKIP']:
                    print("⏭️  Skipping this question (will be added to pending questions)")
                    all_questions_with_status.append({
                        "question": question,
                        "status": "skipped",
                        "answer": ""
                    })
                    question_handled = True
                    break
                
                elif choice in ['A', 'ANSWER']:
                    print("✏️  Please provide your answer:")
                    while True:
                        try:
                            answer = input("   Your answer: ").strip()
                            if answer:
                                answered_questions.append({
                                    "question": question,
                                    "answer": answer
                                })
                                all_questions_with_status.append({
                                    "question": question,
                                    "status": "answered",
                                    "answer": answer
                                })
                                question_handled = True
                                print("✅ Answer recorded!")
                                break
                            else:
                                print("   Please provide a non-empty answer, or choose Skip instead.")
                        except (KeyboardInterrupt, EOFError):
                            print("\n   Skipping this question...")
                            all_questions_with_status.append({
                                "question": question,
                                "status": "skipped",
                                "answer": ""
                            })
                            question_handled = True
                            break
                    break
                
                else:
                    print("   Please enter A (Answer), S (Skip), or Q (Quit)")
                    
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Exiting refinement process...")
                save_progress_to_markdown(all_questions_with_status, schema)
                return answered_questions
    
    print(f"\n🎉 Completed question review!")
    print(f"📊 Questions answered: {len(answered_questions)}/{len(questions)}")
    
    # Save progress to markdown
    save_progress_to_markdown(all_questions_with_status, schema)
    
    return answered_questions


def build_refinement_prompt(schema: Dict[str, Any], answered_questions: List[Dict[str, str]]) -> str:
    """Build AI prompt for schema refinement"""
    
    prompt = f"""You are a senior database architect and data modeling expert. You have been given a MER (Entity-Relationship Model) schema and specific questions with answers from a developer who wants to improve it.

CURRENT SCHEMA:
{json.dumps(schema, indent=2, ensure_ascii=False)}

DEVELOPER QUESTIONS AND ANSWERS:
"""
    
    for i, qa in enumerate(answered_questions, 1):
        prompt += f"{i}. Q: {qa['question']}\n"
        prompt += f"   A: {qa['answer']}\n\n"
    
    prompt += """

INSTRUCTIONS:
1. Analyze the current schema carefully
2. Based on the developer's answers, implement specific improvements to the schema
3. Suggest concrete changes to entities, attributes, relationships, or constraints
4. Consider business logic, data integrity, performance, and best practices
5. Provide the updated schema structure incorporating the developer's requirements
6. Be specific about data types, constraints, and naming conventions

RESPONSE FORMAT:
Provide your response as a JSON object with this structure:
{
  "analysis": "Overall analysis of how the developer's answers improve the schema",
  "implementations": [
    {
      "question": "The original question",
      "user_answer": "The developer's answer",
      "implementation": "How this was implemented in the schema",
      "changes_made": "Specific technical changes made"
    }
  ],
  "improved_schema": {
    "entities": [...],
    "relationships": [...],
    "enums": [...],
    "meta": {...}
  },
  "summary": "Summary of all improvements implemented based on user answers"
}
"""
    
    return prompt


def refine_schema_with_ai(schema: Dict[str, Any], answered_questions: List[Dict[str, str]]) -> Dict[str, Any]:
    """Use AI to refine the schema based on user answered questions"""
    print("\n🤖 Analyzing schema and implementing your improvements...")
    
    prompt = build_refinement_prompt(schema, answered_questions)
    
    try:
        # Call AI model
        response = run_model(prompt, model="gpt-4o", max_output_tokens=8000)
        
        # Parse AI response
        ai_response = json.loads(response)
        
        print("\n" + "="*60)
        print("🤖 AI ANALYSIS & RECOMMENDATIONS")
        print("="*60)
        
        # Display analysis
        if 'analysis' in ai_response:
            print(f"📊 Overall Analysis:")
            print(f"   {ai_response['analysis']}")
        
        # Display implementations
        if 'implementations' in ai_response:
            print(f"\n💡 Implementation Details:")
            for i, impl in enumerate(ai_response['implementations'], 1):
                print(f"\n   Q{i}: {impl.get('question', 'Unknown question')}")
                print(f"   Your Answer: {impl.get('user_answer', 'No answer')}")
                print(f"   Implementation: {impl.get('implementation', 'No implementation')}")
                if impl.get('changes_made'):
                    print(f"   ⚙️ Technical Changes: {impl['changes_made']}")
        
        # Display summary
        if 'summary' in ai_response:
            print(f"\n📋 Summary of Improvements:")
            print(f"   {ai_response['summary']}")
        
        print("="*60)
        
        # Return improved schema if available
        improved_schema = ai_response.get('improved_schema')
        if improved_schema and improved_schema is not None:
            print("\n✨ AI has suggested an improved schema!")
            return improved_schema
        else:
            print("\n📝 No schema changes suggested - current schema looks good!")
            return schema
            
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing AI response: {e}")
        print("Using original schema without changes.")
        return schema
    except Exception as e:
        print(f"❌ Error during AI refinement: {e}")
        print("Using original schema without changes.")
        return schema


def main():
    """Main interactive refinement loop"""
    print("🎯 MER Schema Interactive Refinement")
    print("=====================================")
    
    # Parse command-line arguments
    from_markdown = False
    markdown_file = ""
    input_schema = "schema/mer.json"
    output_schema = "schema/mer2.json"
    
    # Check for --from-markdown flag
    if "--from-markdown" in sys.argv:
        from_markdown = True
        markdown_index = sys.argv.index("--from-markdown")
        if markdown_index + 1 < len(sys.argv):
            markdown_file = sys.argv[markdown_index + 1]
        else:
            print("❌ Error: --from-markdown requires a markdown file path")
            sys.exit(1)
    
    # Handle other arguments
    non_flag_args = [arg for arg in sys.argv[1:] if not arg.startswith("--") and arg != markdown_file]
    if len(non_flag_args) >= 1:
        input_schema = non_flag_args[0]
    if len(non_flag_args) >= 2:
        output_schema = non_flag_args[1]
    
    if from_markdown:
        print(f"📖 Reading answers from markdown: {markdown_file}")
    print(f"📁 Input schema: {input_schema}")
    print(f"💾 Output schema: {output_schema}")
    
    # Load current schema
    print(f"\n📖 Loading schema from {input_schema}...")
    schema = load_mer_schema(input_schema)
    
    # Display current schema
    display_schema_summary(schema)
    
    # Extract questions from schema (open_questions or generate intelligent ones)
    all_questions = extract_questions_from_schema(schema)
    
    if not all_questions:
        print("❌ No questions available. Exiting without changes.")
        return
    
    # Handle different input modes
    if from_markdown:
        # Parse answers from markdown file
        answered_questions = parse_markdown_answers(markdown_file)
        
        if not answered_questions:
            print("❌ No answered questions found in markdown file. Exiting without changes.")
            return
        
        print(f"📊 Found {len(answered_questions)} answered questions in markdown:")
        for i, qa in enumerate(answered_questions, 1):
            print(f"   {i}. {qa['question'][:60]}{'...' if len(qa['question']) > 60 else ''}")
    else:
        # Ask user what they want to do
        print(f"\n🎯 You have {len(all_questions)} questions to review")
        print("="*50)
        print("What would you like to do?")
        print("   1. 💬 Answer questions interactively (one by one)")
        print("   2. 📝 Generate markdown file with all questions")
        print("   3. 🚪 Exit")
        print("="*50)
        
        while True:
            try:
                choice = input("\nEnter your choice (1/2/3): ").strip()
                
                if choice == "1":
                    # Interactive question menu
                    answered_questions = interactive_question_menu(all_questions, schema)
                    
                    if not answered_questions:
                        print("❌ No questions answered. Exiting without changes.")
                        return
                    break
                    
                elif choice == "2":
                    # Generate markdown with all questions as pending
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    markdown_filename = f"questions_{timestamp}.md"
                    markdown_file = generate_questions_markdown(all_questions, schema, markdown_filename)
                    
                    if markdown_file:
                        print(f"✅ All questions saved to markdown: {markdown_file}")
                        print(f"📋 You can now:")
                        print(f"   1. Open {markdown_file} in your editor")
                        print(f"   2. Fill in your answers")
                        print(f"   3. Run: uv run python pipeline/interactive_refinement.py --from-markdown {markdown_file}")
                    return
                    
                elif choice == "3":
                    print("👋 Goodbye!")
                    return
                    
                else:
                    print("❌ Please enter 1, 2, or 3")
                    
            except (KeyboardInterrupt, EOFError):
                print("\n👋 Goodbye!")
                return

    # Only proceed with AI processing if we have answered questions
    if 'answered_questions' in locals() and answered_questions:
        print(f"\n📝 Questions to be processed by AI:")
        for i, qa in enumerate(answered_questions, 1):
            print(f"   {i}. Q: {qa['question']}")
            print(f"      A: {qa['answer']}")
        
        # Confirm with user
        try:
            confirm = input(f"\n🤖 Proceed with AI analysis of {len(answered_questions)} answered questions? (y/N): ").lower().strip()
            if confirm not in ['y', 'yes']:
                print("👋 Refinement cancelled by user.")
                return
        except (KeyboardInterrupt, EOFError):
            print("\n👋 Goodbye!")
            return
    else:
        print("❌ No questions to process. Exiting.")
        return    # AI refinement with answered questions
    improved_schema = refine_schema_with_ai(schema, answered_questions)
    
    # Save improved schema
    save_mer_schema(improved_schema, output_schema)
    
    # Display final summary
    print("\n🎉 Schema refinement complete!")
    display_schema_summary(improved_schema)
    
    print(f"\n✅ Next steps:")
    print(f"   • Review the refined schema: cat {output_schema}")
    print(f"   • Generate Prisma schema: uv run python projectors/prisma/to_prisma.py {output_schema}")
    print(f"   • Continue refining: uv run python pipeline/interactive_refinement.py {output_schema}")


if __name__ == "__main__":
    main()