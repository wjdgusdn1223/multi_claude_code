#!/usr/bin/env python3
"""
Modular Document Templates for Multi-Agent Claude Code
기능별 모듈화된 산출물 구조 및 템플릿 시스템
"""

import os
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

class DocumentModule(Enum):
    """문서 모듈 타입"""
    FUNCTION_SPEC = "function_specification"
    API_SPEC = "api_specification"
    DATA_MODEL = "data_model"
    UI_COMPONENT = "ui_component"
    BUSINESS_RULE = "business_rule"
    TEST_CASE = "test_case"
    DEPLOYMENT_CONFIG = "deployment_config"
    SECURITY_REQUIREMENT = "security_requirement"
    PERFORMANCE_METRIC = "performance_metric"
    USER_STORY = "user_story"

class ModulePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class DocumentModuleTemplate:
    """문서 모듈 템플릿"""
    module_id: str
    module_type: DocumentModule
    title: str
    description: str
    template_structure: Dict[str, Any]
    required_fields: List[str]
    optional_fields: List[str]
    validation_rules: Dict[str, Any]
    dependencies: List[str]
    auto_generation_rules: Dict[str, Any]
    size_estimate: str  # "small", "medium", "large"

class ModularDocumentSystem:
    """모듈화된 문서 시스템"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.templates_dir = self.project_root / "document_templates"
        self.modules_dir = self.project_root / "document_modules"
        
        # 디렉토리 생성
        self.templates_dir.mkdir(exist_ok=True)
        self.modules_dir.mkdir(exist_ok=True)
        
        # 템플릿 초기화
        self.module_templates = self._initialize_templates()
        
    def _initialize_templates(self) -> Dict[str, DocumentModuleTemplate]:
        """기본 템플릿 초기화"""
        templates = {}
        
        # 기능 명세 템플릿
        templates['function_spec'] = DocumentModuleTemplate(
            module_id="function_spec",
            module_type=DocumentModule.FUNCTION_SPEC,
            title="기능 명세서",
            description="개별 기능에 대한 상세 명세",
            template_structure={
                "function_info": {
                    "function_id": "string",
                    "function_name": "string", 
                    "category": "string",
                    "priority": "enum[critical,high,medium,low]"
                },
                "description": {
                    "overview": "text",
                    "detailed_description": "text",
                    "business_value": "text"
                },
                "requirements": {
                    "functional_requirements": "list",
                    "non_functional_requirements": "list",
                    "constraints": "list"
                },
                "user_interaction": {
                    "user_stories": "list",
                    "acceptance_criteria": "list",
                    "user_flows": "list"
                },
                "technical_specs": {
                    "input_parameters": "list",
                    "output_specifications": "list",
                    "business_rules": "list",
                    "validation_rules": "list"
                },
                "dependencies": {
                    "depends_on": "list",
                    "affects": "list",
                    "integrations": "list"
                }
            },
            required_fields=["function_info.function_id", "function_info.function_name", 
                           "description.overview", "requirements.functional_requirements"],
            optional_fields=["user_interaction.user_flows", "technical_specs.validation_rules"],
            validation_rules={
                "function_id": {"pattern": "^F-[0-9]{3}$", "unique": True},
                "priority": {"enum": ["critical", "high", "medium", "low"]},
                "functional_requirements": {"min_items": 1}
            },
            dependencies=["business_requirements"],
            auto_generation_rules={
                "function_id": "auto_increment_pattern",
                "created_date": "current_timestamp",
                "dependencies.affects": "analyze_impact"
            },
            size_estimate="small"
        )
        
        # API 명세 템플릿
        templates['api_spec'] = DocumentModuleTemplate(
            module_id="api_spec",
            module_type=DocumentModule.API_SPEC,
            title="API 명세서",
            description="API 엔드포인트 상세 명세",
            template_structure={
                "api_info": {
                    "endpoint": "string",
                    "method": "enum[GET,POST,PUT,DELETE,PATCH]",
                    "version": "string",
                    "category": "string"
                },
                "description": {
                    "purpose": "text",
                    "functionality": "text"
                },
                "request": {
                    "path_parameters": "list",
                    "query_parameters": "list", 
                    "request_body": "object",
                    "headers": "list"
                },
                "response": {
                    "success_responses": "list",
                    "error_responses": "list",
                    "response_examples": "object"
                },
                "implementation": {
                    "business_logic": "text",
                    "data_access": "list",
                    "external_calls": "list"
                },
                "validation": {
                    "input_validation": "list",
                    "authorization": "text",
                    "rate_limiting": "object"
                }
            },
            required_fields=["api_info.endpoint", "api_info.method", "description.purpose"],
            optional_fields=["validation.rate_limiting", "implementation.external_calls"],
            validation_rules={
                "endpoint": {"pattern": "^/api/v[0-9]+/.*$"},
                "method": {"enum": ["GET", "POST", "PUT", "DELETE", "PATCH"]}
            },
            dependencies=["function_spec"],
            auto_generation_rules={
                "created_date": "current_timestamp",
                "response.error_responses": "standard_error_templates"
            },
            size_estimate="medium"
        )
        
        # UI 컴포넌트 템플릿
        templates['ui_component'] = DocumentModuleTemplate(
            module_id="ui_component",
            module_type=DocumentModule.UI_COMPONENT,
            title="UI 컴포넌트 명세서",
            description="사용자 인터페이스 컴포넌트 상세 명세",
            template_structure={
                "component_info": {
                    "component_id": "string",
                    "component_name": "string",
                    "component_type": "enum[page,modal,form,list,card,button]",
                    "parent_page": "string"
                },
                "design_specs": {
                    "layout": "text",
                    "styling": "object",
                    "responsive_behavior": "text",
                    "accessibility_features": "list"
                },
                "functionality": {
                    "user_interactions": "list",
                    "state_management": "text",
                    "data_binding": "list"
                },
                "api_integration": {
                    "api_calls": "list",
                    "data_flow": "text",
                    "error_handling": "text"
                },
                "validation": {
                    "form_validation": "list",
                    "business_rules": "list"
                }
            },
            required_fields=["component_info.component_id", "component_info.component_name"],
            optional_fields=["validation.business_rules"],
            validation_rules={
                "component_id": {"pattern": "^UI-[0-9]{3}$", "unique": True}
            },
            dependencies=["ui_designs", "api_spec"],
            auto_generation_rules={
                "component_id": "auto_increment_pattern"
            },
            size_estimate="medium"
        )
        
        # 데이터 모델 템플릿
        templates['data_model'] = DocumentModuleTemplate(
            module_id="data_model",
            module_type=DocumentModule.DATA_MODEL,
            title="데이터 모델 명세서",
            description="데이터베이스 테이블 및 관계 명세",
            template_structure={
                "model_info": {
                    "table_name": "string",
                    "model_name": "string",
                    "description": "text"
                },
                "fields": {
                    "primary_key": "object",
                    "fields": "list",
                    "foreign_keys": "list",
                    "indexes": "list"
                },
                "relationships": {
                    "has_many": "list",
                    "belongs_to": "list",
                    "many_to_many": "list"
                },
                "constraints": {
                    "unique_constraints": "list",
                    "check_constraints": "list",
                    "business_rules": "list"
                },
                "operations": {
                    "create_operations": "list",
                    "read_operations": "list",
                    "update_operations": "list",
                    "delete_operations": "list"
                }
            },
            required_fields=["model_info.table_name", "fields.primary_key", "fields.fields"],
            optional_fields=["relationships.many_to_many"],
            validation_rules={
                "table_name": {"pattern": "^[a-z_]+$"}
            },
            dependencies=["function_spec"],
            auto_generation_rules={
                "model_name": "pascal_case_from_table_name"
            },
            size_estimate="small"
        )
        
        # 테스트 케이스 템플릿
        templates['test_case'] = DocumentModuleTemplate(
            module_id="test_case",
            module_type=DocumentModule.TEST_CASE,
            title="테스트 케이스 명세서",
            description="개별 기능에 대한 테스트 케이스",
            template_structure={
                "test_info": {
                    "test_id": "string",
                    "test_name": "string",
                    "test_type": "enum[unit,integration,e2e,performance]",
                    "priority": "enum[critical,high,medium,low]"
                },
                "test_target": {
                    "function_id": "string",
                    "component_id": "string",
                    "api_endpoint": "string"
                },
                "test_scenario": {
                    "description": "text",
                    "preconditions": "list",
                    "test_steps": "list",
                    "expected_results": "list"
                },
                "test_data": {
                    "input_data": "object",
                    "mock_data": "object",
                    "test_fixtures": "list"
                },
                "automation": {
                    "automatable": "boolean",
                    "test_framework": "string",
                    "automation_script": "text"
                }
            },
            required_fields=["test_info.test_id", "test_info.test_name", "test_scenario.description"],
            optional_fields=["automation.automation_script"],
            validation_rules={
                "test_id": {"pattern": "^T-[0-9]{3}$", "unique": True}
            },
            dependencies=["function_spec", "api_spec"],
            auto_generation_rules={
                "test_id": "auto_increment_pattern"
            },
            size_estimate="small"
        )
        
        return templates
    
    def create_module(self, 
                     module_type: DocumentModule, 
                     role_id: str,
                     module_data: Dict[str, Any],
                     auto_fill: bool = True) -> Dict[str, Any]:
        """새 문서 모듈 생성"""
        
        template = self.module_templates.get(module_type.value)
        if not template:
            raise ValueError(f"Unknown module type: {module_type}")
        
        # 자동 생성 규칙 적용
        if auto_fill:
            module_data = self._apply_auto_generation_rules(template, module_data)
        
        # 유효성 검사
        validation_result = self._validate_module_data(template, module_data)
        if not validation_result['valid']:
            raise ValueError(f"Validation failed: {validation_result['errors']}")
        
        # 모듈 문서 생성
        module_doc = {
            'metadata': {
                'module_id': module_data.get('module_id', self._generate_module_id(module_type)),
                'module_type': module_type.value,
                'title': template.title,
                'created_by': role_id,
                'created_at': datetime.now().isoformat(),
                'version': '1.0',
                'status': 'draft'
            },
            'content': module_data,
            'template_version': '1.0'
        }
        
        # 파일 저장
        module_file = self._save_module(module_doc)
        
        print(f"✅ 모듈 생성 완료: {module_file}")
        return module_doc
    
    def generate_modular_deliverable(self, 
                                   role_id: str,
                                   deliverable_name: str,
                                   module_ids: List[str],
                                   template_config: Dict[str, Any] = None) -> str:
        """모듈들을 조합하여 최종 산출물 생성"""
        
        # 모듈 로드
        modules = []
        for module_id in module_ids:
            module = self._load_module(module_id)
            if module:
                modules.append(module)
            else:
                print(f"⚠️ 모듈을 찾을 수 없습니다: {module_id}")
        
        if not modules:
            raise ValueError("유효한 모듈이 없습니다.")
        
        # 의존성 순서 정렬
        sorted_modules = self._sort_modules_by_dependency(modules)
        
        # 최종 문서 생성
        final_document = self._assemble_document(
            role_id=role_id,
            deliverable_name=deliverable_name,
            modules=sorted_modules,
            template_config=template_config
        )
        
        # 파일 저장
        output_file = self.project_root / "roles" / role_id / "deliverables" / f"{deliverable_name}.md"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(final_document)
        
        print(f"✅ 모듈형 산출물 생성 완료: {output_file}")
        return str(output_file)
    
    def suggest_modules_for_function(self, function_description: str) -> List[Dict[str, Any]]:
        """기능 설명을 바탕으로 필요한 모듈 제안"""
        suggestions = []
        
        # 키워드 기반 모듈 추천
        keywords = function_description.lower().split()
        
        # API 관련 키워드
        if any(word in keywords for word in ['api', 'endpoint', 'rest', 'http']):
            suggestions.append({
                'module_type': DocumentModule.API_SPEC,
                'reason': 'API 관련 키워드 감지',
                'priority': ModulePriority.HIGH
            })
        
        # UI 관련 키워드
        if any(word in keywords for word in ['ui', 'interface', 'form', 'page', 'component']):
            suggestions.append({
                'module_type': DocumentModule.UI_COMPONENT,
                'reason': 'UI 관련 키워드 감지',
                'priority': ModulePriority.HIGH
            })
        
        # 데이터 관련 키워드
        if any(word in keywords for word in ['data', 'database', 'model', 'table', 'crud']):
            suggestions.append({
                'module_type': DocumentModule.DATA_MODEL,
                'reason': '데이터 관련 키워드 감지',
                'priority': ModulePriority.MEDIUM
            })
        
        # 항상 기본 모듈들 추천
        suggestions.extend([
            {
                'module_type': DocumentModule.FUNCTION_SPEC,
                'reason': '기본 기능 명세',
                'priority': ModulePriority.CRITICAL
            },
            {
                'module_type': DocumentModule.TEST_CASE,
                'reason': '품질 보증을 위한 테스트',
                'priority': ModulePriority.HIGH
            }
        ])
        
        return suggestions
    
    def create_function_module_set(self, 
                                 role_id: str,
                                 function_name: str,
                                 function_description: str,
                                 additional_specs: Dict[str, Any] = None) -> List[str]:
        """기능에 대한 완전한 모듈 세트 생성"""
        
        module_ids = []
        base_id = function_name.lower().replace(' ', '_')
        
        # 1. 기능 명세 모듈
        func_spec_data = {
            'function_info': {
                'function_id': f"F-{len(module_ids)+1:03d}",
                'function_name': function_name,
                'category': additional_specs.get('category', 'general'),
                'priority': additional_specs.get('priority', 'medium')
            },
            'description': {
                'overview': function_description,
                'detailed_description': additional_specs.get('detailed_description', ''),
                'business_value': additional_specs.get('business_value', '')
            },
            'requirements': {
                'functional_requirements': additional_specs.get('functional_requirements', []),
                'non_functional_requirements': additional_specs.get('non_functional_requirements', [])
            }
        }
        
        func_module = self.create_module(
            DocumentModule.FUNCTION_SPEC,
            role_id,
            func_spec_data
        )
        module_ids.append(func_module['metadata']['module_id'])
        
        # 2. API 명세 모듈 (API 기능인 경우)
        if additional_specs and additional_specs.get('has_api', False):
            api_spec_data = {
                'api_info': {
                    'endpoint': f"/api/v1/{base_id}",
                    'method': additional_specs.get('api_method', 'GET'),
                    'version': '1.0',
                    'category': additional_specs.get('category', 'general')
                },
                'description': {
                    'purpose': function_description,
                    'functionality': additional_specs.get('api_functionality', '')
                }
            }
            
            api_module = self.create_module(
                DocumentModule.API_SPEC,
                role_id,
                api_spec_data
            )
            module_ids.append(api_module['metadata']['module_id'])
        
        # 3. UI 컴포넌트 모듈 (UI 기능인 경우)
        if additional_specs and additional_specs.get('has_ui', False):
            ui_spec_data = {
                'component_info': {
                    'component_id': f"UI-{len(module_ids)+1:03d}",
                    'component_name': f"{function_name} Component",
                    'component_type': additional_specs.get('ui_type', 'page'),
                    'parent_page': additional_specs.get('parent_page', 'main')
                },
                'functionality': {
                    'user_interactions': additional_specs.get('user_interactions', []),
                    'state_management': additional_specs.get('state_management', '')
                }
            }
            
            ui_module = self.create_module(
                DocumentModule.UI_COMPONENT,
                role_id,
                ui_spec_data
            )
            module_ids.append(ui_module['metadata']['module_id'])
        
        # 4. 데이터 모델 모듈 (데이터 관련 기능인 경우)
        if additional_specs and additional_specs.get('has_data_model', False):
            data_model_data = {
                'model_info': {
                    'table_name': additional_specs.get('table_name', base_id),
                    'model_name': additional_specs.get('model_name', function_name.title().replace(' ', '')),
                    'description': f"{function_name}을 위한 데이터 모델"
                },
                'fields': {
                    'primary_key': {'name': 'id', 'type': 'integer', 'auto_increment': True},
                    'fields': additional_specs.get('fields', [])
                }
            }
            
            data_module = self.create_module(
                DocumentModule.DATA_MODEL,
                role_id,
                data_model_data
            )
            module_ids.append(data_module['metadata']['module_id'])
        
        # 5. 테스트 케이스 모듈
        test_spec_data = {
            'test_info': {
                'test_id': f"T-{len(module_ids)+1:03d}",
                'test_name': f"{function_name} Test",
                'test_type': 'integration',
                'priority': additional_specs.get('priority', 'medium')
            },
            'test_target': {
                'function_id': func_spec_data['function_info']['function_id']
            },
            'test_scenario': {
                'description': f"{function_name} 기능 테스트",
                'preconditions': additional_specs.get('test_preconditions', []),
                'test_steps': additional_specs.get('test_steps', []),
                'expected_results': additional_specs.get('expected_results', [])
            }
        }
        
        test_module = self.create_module(
            DocumentModule.TEST_CASE,
            role_id,
            test_spec_data
        )
        module_ids.append(test_module['metadata']['module_id'])
        
        print(f"✅ {function_name}에 대한 {len(module_ids)}개 모듈 생성 완료")
        return module_ids
    
    # Helper methods
    def _apply_auto_generation_rules(self, template: DocumentModuleTemplate, data: Dict[str, Any]) -> Dict[str, Any]:
        """자동 생성 규칙 적용"""
        for field_path, rule in template.auto_generation_rules.items():
            if rule == "current_timestamp":
                self._set_nested_value(data, field_path, datetime.now().isoformat())
            elif rule == "auto_increment_pattern":
                # 간단한 자동 증가 ID 생성
                self._set_nested_value(data, field_path, self._generate_auto_id(template.module_type))
        
        return data
    
    def _set_nested_value(self, data: Dict[str, Any], path: str, value: Any):
        """중첩된 딕셔너리에 값 설정"""
        keys = path.split('.')
        current = data
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def _generate_auto_id(self, module_type: DocumentModule) -> str:
        """자동 ID 생성"""
        type_prefix = {
            DocumentModule.FUNCTION_SPEC: "F",
            DocumentModule.API_SPEC: "API",
            DocumentModule.UI_COMPONENT: "UI",
            DocumentModule.DATA_MODEL: "DM",
            DocumentModule.TEST_CASE: "T"
        }
        
        prefix = type_prefix.get(module_type, "M")
        # 실제로는 기존 ID들을 확인하여 다음 번호 생성
        return f"{prefix}-001"
    
    def _validate_module_data(self, template: DocumentModuleTemplate, data: Dict[str, Any]) -> Dict[str, Any]:
        """모듈 데이터 유효성 검사"""
        errors = []
        
        # 필수 필드 검사
        for field_path in template.required_fields:
            if not self._has_nested_value(data, field_path):
                errors.append(f"Required field missing: {field_path}")
        
        # 유효성 검사 규칙 적용
        for field_path, rules in template.validation_rules.items():
            value = self._get_nested_value(data, field_path)
            if value is not None:
                # 패턴 검사
                if 'pattern' in rules:
                    import re
                    if not re.match(rules['pattern'], str(value)):
                        errors.append(f"Pattern validation failed for {field_path}: {value}")
                
                # 열거형 검사
                if 'enum' in rules:
                    if value not in rules['enum']:
                        errors.append(f"Invalid enum value for {field_path}: {value}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _has_nested_value(self, data: Dict[str, Any], path: str) -> bool:
        """중첩된 값 존재 확인"""
        try:
            self._get_nested_value(data, path)
            return True
        except (KeyError, TypeError):
            return False
    
    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """중첩된 값 조회"""
        keys = path.split('.')
        current = data
        
        for key in keys:
            current = current[key]
        
        return current
    
    def _generate_module_id(self, module_type: DocumentModule) -> str:
        """모듈 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{module_type.value}_{timestamp}"
    
    def _save_module(self, module_doc: Dict[str, Any]) -> str:
        """모듈 저장"""
        module_id = module_doc['metadata']['module_id']
        module_file = self.modules_dir / f"{module_id}.json"
        
        with open(module_file, 'w', encoding='utf-8') as f:
            json.dump(module_doc, f, indent=2, ensure_ascii=False, default=str)
        
        return str(module_file)
    
    def _load_module(self, module_id: str) -> Optional[Dict[str, Any]]:
        """모듈 로드"""
        module_file = self.modules_dir / f"{module_id}.json"
        
        if module_file.exists():
            try:
                with open(module_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"모듈 로드 실패 ({module_id}): {str(e)}")
        
        return None
    
    def _sort_modules_by_dependency(self, modules: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """의존성 순서로 모듈 정렬"""
        # 간단한 구현 - 실제로는 더 복잡한 의존성 해결 알고리즘 필요
        dependency_order = [
            DocumentModule.FUNCTION_SPEC,
            DocumentModule.DATA_MODEL,
            DocumentModule.API_SPEC,
            DocumentModule.UI_COMPONENT,
            DocumentModule.TEST_CASE
        ]
        
        def get_order(module):
            module_type = DocumentModule(module['metadata']['module_type'])
            try:
                return dependency_order.index(module_type)
            except ValueError:
                return 999
        
        return sorted(modules, key=get_order)
    
    def _assemble_document(self, 
                          role_id: str,
                          deliverable_name: str,
                          modules: List[Dict[str, Any]],
                          template_config: Dict[str, Any] = None) -> str:
        """모듈들을 조합하여 최종 문서 생성"""
        
        doc_parts = []
        
        # 문서 헤더
        doc_parts.append(f"# {deliverable_name}")
        doc_parts.append(f"")
        doc_parts.append(f"**작성자**: {role_id}")
        doc_parts.append(f"**작성일**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        doc_parts.append(f"**모듈 수**: {len(modules)}")
        doc_parts.append(f"")
        doc_parts.append(f"## 개요")
        doc_parts.append(f"본 문서는 {len(modules)}개의 모듈로 구성된 {deliverable_name}입니다.")
        doc_parts.append(f"")
        
        # 목차
        doc_parts.append(f"## 목차")
        for i, module in enumerate(modules, 1):
            title = module['metadata']['title']
            module_id = module['metadata']['module_id']
            doc_parts.append(f"{i}. {title} ({module_id})")
        doc_parts.append(f"")
        
        # 각 모듈 내용
        for i, module in enumerate(modules, 1):
            doc_parts.append(f"## {i}. {module['metadata']['title']}")
            doc_parts.append(f"")
            doc_parts.append(f"**모듈 ID**: {module['metadata']['module_id']}")
            doc_parts.append(f"**모듈 타입**: {module['metadata']['module_type']}")
            doc_parts.append(f"**버전**: {module['metadata']['version']}")
            doc_parts.append(f"")
            
            # 모듈 내용을 마크다운으로 변환
            content_md = self._convert_module_content_to_markdown(module['content'])
            doc_parts.append(content_md)
            doc_parts.append(f"")
            doc_parts.append(f"---")
            doc_parts.append(f"")
        
        # 문서 푸터
        doc_parts.append(f"## 문서 정보")
        doc_parts.append(f"- **생성일시**: {datetime.now().isoformat()}")
        doc_parts.append(f"- **생성 시스템**: Modular Document System v1.0")
        doc_parts.append(f"- **포함 모듈**: {', '.join(m['metadata']['module_id'] for m in modules)}")
        
        return '\n'.join(doc_parts)
    
    def _convert_module_content_to_markdown(self, content: Dict[str, Any]) -> str:
        """모듈 내용을 마크다운으로 변환"""
        md_parts = []
        
        def convert_value(key: str, value: Any, level: int = 3) -> List[str]:
            parts = []
            indent = "#" * level
            
            if isinstance(value, dict):
                parts.append(f"{indent} {key.replace('_', ' ').title()}")
                for sub_key, sub_value in value.items():
                    parts.extend(convert_value(sub_key, sub_value, level + 1))
            elif isinstance(value, list):
                parts.append(f"{indent} {key.replace('_', ' ').title()}")
                for item in value:
                    if isinstance(item, str):
                        parts.append(f"- {item}")
                    else:
                        parts.append(f"- {str(item)}")
            else:
                parts.append(f"**{key.replace('_', ' ').title()}**: {value}")
            
            return parts
        
        for key, value in content.items():
            md_parts.extend(convert_value(key, value))
            md_parts.append("")
        
        return '\n'.join(md_parts)

def main():
    """테스트 및 데모"""
    modular_system = ModularDocumentSystem("/home/jungh/workspace/multi_claude_code_sample")
    
    # 예시: 사용자 로그인 기능에 대한 모듈 세트 생성
    module_ids = modular_system.create_function_module_set(
        role_id="business_analyst",
        function_name="사용자 로그인",
        function_description="사용자가 이메일과 비밀번호로 시스템에 로그인하는 기능",
        additional_specs={
            'category': 'authentication',
            'priority': 'critical',
            'has_api': True,
            'api_method': 'POST',
            'has_ui': True,
            'ui_type': 'form',
            'has_data_model': True,
            'table_name': 'users',
            'fields': [
                {'name': 'email', 'type': 'string', 'required': True},
                {'name': 'password_hash', 'type': 'string', 'required': True},
                {'name': 'last_login', 'type': 'datetime', 'required': False}
            ]
        }
    )
    
    # 최종 산출물 생성
    deliverable_file = modular_system.generate_modular_deliverable(
        role_id="business_analyst",
        deliverable_name="user_login_specification",
        module_ids=module_ids
    )
    
    print(f"✅ 모듈화된 산출물 생성 완료: {deliverable_file}")

if __name__ == "__main__":
    main()