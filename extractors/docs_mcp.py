#!/usr/bin/env python3
"""
Documents MCP Client - Extract business context from documentation files
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import subprocess
import tempfile

# Document processing imports (with fallbacks)
try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# DOC files will be handled via external tools (antiword, textutil)

class DocumentsMCPClient:
    """MCP client to extract business context from documentation files"""
    
    def __init__(self, docs_dir: str = "./docs"):
        self.docs_dir = Path(docs_dir)
        self.supported_extensions = {'.md', '.txt', '.json', '.yaml', '.yml', '.pdf', '.docx', '.doc'}
        self._check_dependencies()
        
    def extract_documents_context(self) -> Dict[str, Any]:
        """Extract complete context from documentation directory"""
        if not self.docs_dir.exists():
            print(f"📁 Documents directory not found: {self.docs_dir}")
            return self._empty_context()
        
        print(f"📚 Reading documents from: {self.docs_dir}")
        
        context = {
            "glossary": [],
            "rules": [],
            "enums": [],
            "sources": []
        }
        
        # Process all supported files
        for file_path in self.docs_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in self.supported_extensions:
                print(f"📄 Processing: {file_path.name}")
                file_context = self._process_file(file_path)
                context = self._merge_context(context, file_context)
        
        print(f"✅ Extracted: {len(context['glossary'])} terms, {len(context['rules'])} rules, {len(context['enums'])} enums")
        return context
    
    def _process_file(self, file_path: Path) -> Dict[str, Any]:
        """Process a single documentation file"""
        try:
            source_ref = f"doc:{file_path.name}"
            
            context = {
                "glossary": [],
                "rules": [],
                "enums": [],
                "sources": [source_ref]
            }
            
            # Extract content based on file type
            content = self._extract_text_content(file_path)
            if not content:
                print(f"⚠️  No content extracted from {file_path.name}")
                return self._empty_context()
            
            # Parse based on file type
            if file_path.suffix.lower() == '.json':
                context.update(self._parse_json_file(content, source_ref))
            elif file_path.suffix.lower() in {'.yaml', '.yml'}:
                context.update(self._parse_yaml_file(content, source_ref))
            else:
                # Text-based files (including extracted text from PDF/DOC/DOCX)
                context.update(self._parse_text_file(content, source_ref))
            
            return context
            
        except Exception as e:
            print(f"⚠️  Error processing {file_path.name}: {e}")
            return self._empty_context()
    
    def _extract_text_content(self, file_path: Path) -> str:
        """Extract text content from various file formats"""
        try:
            suffix = file_path.suffix.lower()
            
            if suffix == '.pdf':
                return self._extract_pdf_text(file_path)
            elif suffix == '.docx':
                return self._extract_docx_text(file_path)
            elif suffix == '.doc':
                return self._extract_doc_text(file_path)
            else:
                # Plain text files
                return file_path.read_text(encoding='utf-8')
                
        except Exception as e:
            print(f"⚠️  Error extracting text from {file_path.name}: {e}")
            return ""
    
    def _extract_pdf_text(self, file_path: Path) -> str:
        """Extract text from PDF files"""
        if not PDF_AVAILABLE:
            print(f"⚠️  PyPDF2 not available, skipping {file_path.name}")
            return ""
        
        try:
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        except Exception as e:
            print(f"⚠️  Error reading PDF {file_path.name}: {e}")
            return ""
    
    def _extract_docx_text(self, file_path: Path) -> str:
        """Extract text from DOCX files"""
        if not DOCX_AVAILABLE:
            print(f"⚠️  python-docx not available, skipping {file_path.name}")
            return ""
        
        try:
            doc = DocxDocument(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            print(f"⚠️  Error reading DOCX {file_path.name}: {e}")
            return ""
    
    def _extract_doc_text(self, file_path: Path) -> str:
        """Extract text from DOC files (legacy Word format)"""
        # For .doc files, we'll try to use antiword or textutil (macOS) as fallback
        try:
            # Try antiword first (if available)
            result = subprocess.run(['antiword', str(file_path)], 
                                 capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        try:
            # Try textutil on macOS
            result = subprocess.run(['textutil', '-convert', 'txt', '-stdout', str(file_path)], 
                                 capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                return result.stdout
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        print(f"⚠️  Cannot extract text from .doc file {file_path.name}. Install antiword or use macOS textutil.")
        return ""
    
    def _check_dependencies(self):
        """Check and warn about missing dependencies"""
        missing = []
        
        if not PDF_AVAILABLE:
            missing.append("PyPDF2 (for PDF support)")
        if not DOCX_AVAILABLE:
            missing.append("python-docx (for DOCX support)")
        
        if missing:
            print(f"📦 Optional dependencies missing: {', '.join(missing)}")
            print(f"   Install with: uv add {' '.join(['PyPDF2' if 'PyPDF2' in dep else 'python-docx' for dep in missing])}")
            print(f"   These file types will be skipped if encountered.")
    
    def _parse_json_file(self, content: str, source_ref: str) -> Dict[str, Any]:
        """Parse structured JSON documentation"""
        try:
            data = json.loads(content)
            context = self._empty_context()
            
            # Look for structured sections
            if isinstance(data, dict):
                if "glossary" in data:
                    context["glossary"] = self._normalize_glossary(data["glossary"], source_ref)
                if "rules" in data:
                    context["rules"] = self._normalize_rules(data["rules"], source_ref)
                if "enums" in data:
                    context["enums"] = self._normalize_enums(data["enums"], source_ref)
            
            return context
            
        except json.JSONDecodeError:
            return self._empty_context()
    
    def _parse_yaml_file(self, content: str, source_ref: str) -> Dict[str, Any]:
        """Parse YAML documentation (basic implementation)"""
        # For now, treat as text - could add proper YAML parsing later
        return self._parse_text_file(content, source_ref)
    
    def _parse_text_file(self, content: str, source_ref: str) -> Dict[str, Any]:
        """Parse markdown/text files for business context"""
        context = self._empty_context()
        
        # Extract glossary terms (## Terms, ### Definition patterns)
        glossary_terms = self._extract_glossary_from_text(content, source_ref)
        context["glossary"].extend(glossary_terms)
        
        # Extract business rules (patterns like "Business Rule:", "Rule:", etc.)
        rules = self._extract_rules_from_text(content, source_ref)
        context["rules"].extend(rules)
        
        # Extract enums (patterns like "Status:", "Type:", lists)
        enums = self._extract_enums_from_text(content, source_ref)
        context["enums"].extend(enums)
        
        return context
    
    def _extract_glossary_from_text(self, content: str, source_ref: str) -> List[Dict[str, Any]]:
        """Extract glossary terms from text content"""
        terms = []
        
        # Pattern 1: ## Term or **Term**: Definition
        term_patterns = [
            r'(?:##\s+|###\s+|\*\*)([\w\s]+?)(?:\*\*)?:?\s*\n(.*?)(?=\n##|\n###|\n\*\*|\Z)',
            r'\*\*([\w\s]+?)\*\*:?\s*(.*?)(?=\n|$)',
            r'^([A-Z][a-zA-Z\s]{2,}):\s*(.*?)(?=\n|$)'
        ]
        
        for pattern in term_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                term = match.group(1).strip()
                definition = match.group(2).strip()
                
                if len(term) <= 50 and len(definition) > 10:  # Basic quality filter
                    terms.append({
                        "term": term,
                        "definition": definition,
                        "aliases": [],
                        "sources": [source_ref]
                    })
        
        return terms
    
    def _extract_rules_from_text(self, content: str, source_ref: str) -> List[Dict[str, Any]]:
        """Extract business rules from text content"""
        rules = []
        
        # Pattern: Look for "Rule:", "Business Rule:", "BR:", etc.
        rule_patterns = [
            r'(?:Business\s+)?Rule\s*\d*:?\s*(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'BR\d+:?\s*(.*?)(?=\n\n|\n[A-Z]|\Z)',
            r'Constraint:?\s*(.*?)(?=\n\n|\n[A-Z]|\Z)'
        ]
        
        for pattern in rule_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            for match in matches:
                rule_text = match.group(1).strip()
                
                if len(rule_text) > 10:  # Basic quality filter
                    rules.append({
                        "kind": "business_rule",
                        "description": rule_text,
                        "sources": [source_ref]
                    })
        
        return rules
    
    def _extract_enums_from_text(self, content: str, source_ref: str) -> List[Dict[str, Any]]:
        """Extract enum-like structures from text"""
        enums = []
        
        # Pattern: "Status:" followed by list items
        enum_patterns = [
            r'([\w\s]+?)(?:Status|Type|State|Category):?\s*\n((?:\s*[-*]\s*\w+.*\n?)+)',
            r'([\w\s]+?):\s*\n((?:\s*\d+\.\s*\w+.*\n?)+)'
        ]
        
        for pattern in enum_patterns:
            matches = re.finditer(pattern, content, re.MULTILINE)
            for match in matches:
                enum_name = match.group(1).strip()
                values_text = match.group(2)
                
                # Extract individual values
                values = []
                for line in values_text.split('\n'):
                    line = line.strip()
                    if line and (line.startswith('-') or line.startswith('*') or re.match(r'\d+\.', line)):
                        value = re.sub(r'^[-*\d.]\s*', '', line).strip()
                        if value:
                            values.append(value)
                
                if len(values) >= 2:  # Must have at least 2 values to be an enum
                    enums.append({
                        "name": enum_name,
                        "values": values,
                        "sources": [source_ref]
                    })
        
        return enums
    
    def _normalize_glossary(self, glossary_data: Any, source_ref: str) -> List[Dict[str, Any]]:
        """Normalize glossary data to standard format"""
        if not isinstance(glossary_data, list):
            return []
        
        normalized = []
        for item in glossary_data:
            if isinstance(item, dict) and "term" in item and "definition" in item:
                normalized.append({
                    "term": item["term"],
                    "definition": item["definition"],
                    "aliases": item.get("aliases", []),
                    "sources": [source_ref]
                })
        
        return normalized
    
    def _normalize_rules(self, rules_data: Any, source_ref: str) -> List[Dict[str, Any]]:
        """Normalize rules data to standard format"""
        if not isinstance(rules_data, list):
            return []
        
        normalized = []
        for item in rules_data:
            if isinstance(item, dict):
                normalized.append({
                    "kind": item.get("kind", "business_rule"),
                    "description": item.get("description", str(item)),
                    "from": item.get("from"),
                    "to": item.get("to"),
                    "type": item.get("type"),
                    "sources": [source_ref]
                })
        
        return normalized
    
    def _normalize_enums(self, enums_data: Any, source_ref: str) -> List[Dict[str, Any]]:
        """Normalize enums data to standard format"""
        if not isinstance(enums_data, list):
            return []
        
        normalized = []
        for item in enums_data:
            if isinstance(item, dict) and "name" in item and "values" in item:
                normalized.append({
                    "name": item["name"],
                    "values": item["values"],
                    "sources": [source_ref]
                })
        
        return normalized
    
    def _merge_context(self, base_context: Dict[str, Any], new_context: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two context dictionaries"""
        merged = base_context.copy()
        
        for key in ["glossary", "rules", "enums", "sources"]:
            if key in new_context:
                merged[key].extend(new_context[key])
        
        return merged
    
    def _empty_context(self) -> Dict[str, Any]:
        """Return empty context structure"""
        return {
            "glossary": [],
            "rules": [],
            "enums": [],
            "sources": []
        }


def extract_doc_facts(context_pack: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts definitions and rules from the 'documents' section of the context pack.
    Legacy function for compatibility.
    """
    docs = context_pack.get("documents", {})
    return {
        "glossary": docs.get("glossary", []),
        "rules": docs.get("rules", []),
        "enums": docs.get("enums", []),
        "sources": docs.get("sources", [])
    }


def main():
    """Test the documents MCP client"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    docs_dir = os.getenv("DOCS_RESOURCES_DIR", "./docs")
    client = DocumentsMCPClient(docs_dir)
    
    context = client.extract_documents_context()
    
    print("\n📊 EXTRACTED CONTEXT:")
    print(f"📚 Glossary terms: {len(context['glossary'])}")
    for term in context['glossary'][:3]:  # Show first 3
        print(f"   • {term['term']}: {term['definition'][:50]}...")
    
    print(f"📋 Business rules: {len(context['rules'])}")
    for rule in context['rules'][:3]:  # Show first 3
        print(f"   • {rule.get('description', str(rule))[:50]}...")
    
    print(f"🏷️  Enums: {len(context['enums'])}")
    for enum in context['enums'][:3]:  # Show first 3
        print(f"   • {enum['name']}: {enum['values']}")


if __name__ == "__main__":
    main()
