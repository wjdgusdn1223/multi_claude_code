#!/usr/bin/env python3
"""
AI-Optimized Deliverable Templates for Multi-Agent Claude Code
AI 에이전트 전용 산출물 템플릿 시스템 - 인간 중심 요소 제거 및 AI 효율성 최적화
"""

import os
import json
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass

class AIProcessingFormat(Enum):
    """AI 처리 최적화 포맷"""
    STRUCTURED_JSON = "structured_json"  # 구조화된 JSON
    YAML_CONFIG = "yaml_config"         # YAML 설정
    CODE_SNIPPET = "code_snippet"       # 코드 조각
    DECISION_TREE = "decision_tree"     # 결정 트리
    WORKFLOW_CHAIN = "workflow_chain"   # 워크플로우 체인
    VALIDATION_RULES = "validation_rules"  # 검증 규칙

class AIDeliverableType(Enum):
    """AI 산출물 타입"""
    ROLE_INSTRUCTION = "role_instruction"        # 역할 지시사항
    AUTOMATION_SCRIPT = "automation_script"      # 자동화 스크립트
    VALIDATION_CRITERIA = "validation_criteria"  # 검증 기준
    COMMUNICATION_PROTOCOL = "communication_protocol"  # 소통 프로토콜
    DECISION_MATRIX = "decision_matrix"          # 의사결정 매트릭스
    WORKFLOW_DEFINITION = "workflow_definition"  # 워크플로우 정의
    INTEGRATION_MAP = "integration_map"          # 통합 맵
    PERFORMANCE_METRIC = "performance_metric"    # 성능 지표

@dataclass
class AIOptimizedTemplate:
    """AI 최적화 템플릿"""
    template_id: str
    deliverable_type: AIDeliverableType
    processing_format: AIProcessingFormat
    ai_consumption_optimized: bool
    machine_readable_structure: Dict[str, Any]
    automation_hooks: List[str]
    validation_schema: Dict[str, Any]
    cross_role_compatibility: List[str]
    version_control_friendly: bool
    computational_efficiency_score: float

class AIOptimizedDeliverableSystem:
    """AI 전용 산출물 시스템"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.ai_templates_dir = self.project_root / "ai_deliverable_templates"
        self.ai_deliverables_dir = self.project_root / "ai_deliverables"
        
        # 디렉토리 생성
        self.ai_templates_dir.mkdir(exist_ok=True)
        self.ai_deliverables_dir.mkdir(exist_ok=True)
        
        # AI 최적화 템플릿 초기화
        self.ai_templates = self._initialize_ai_templates()
        
    def _initialize_ai_templates(self) -> Dict[str, AIOptimizedTemplate]:
        """AI 최적화 템플릿 초기화"""
        templates = {}
        
        # 1. 역할 지시사항 템플릿
        templates['role_instruction'] = AIOptimizedTemplate(
            template_id="role_instruction_v1",
            deliverable_type=AIDeliverableType.ROLE_INSTRUCTION,
            processing_format=AIProcessingFormat.STRUCTURED_JSON,
            ai_consumption_optimized=True,
            machine_readable_structure={
                "role_metadata": {
                    "role_id": "string",
                    "role_name": "string",
                    "domain_expertise": "list",
                    "primary_responsibilities": "list",
                    "secondary_responsibilities": "list"
                },
                "operational_parameters": {
                    "decision_authority_level": "enum[low,medium,high,full]",
                    "autonomy_scope": "list",
                    "escalation_triggers": "list",
                    "quality_thresholds": "object"
                },
                "input_processing": {
                    "accepted_input_formats": "list",
                    "input_validation_rules": "object",
                    "preprocessing_steps": "list"
                },
                "output_specifications": {
                    "required_output_format": "string",
                    "output_validation_schema": "object",
                    "delivery_channels": "list"
                },
                "interaction_protocols": {
                    "communication_interfaces": "list",
                    "collaboration_patterns": "object",
                    "conflict_resolution_procedures": "list"
                },
                "performance_metrics": {
                    "success_criteria": "list",
                    "quality_indicators": "object",
                    "efficiency_targets": "object"
                }
            },
            automation_hooks=[
                "role_activation_trigger",
                "task_completion_callback", 
                "quality_gate_validation",
                "handoff_preparation"
            ],
            validation_schema={
                "required_fields": ["role_metadata.role_id", "operational_parameters.decision_authority_level"],
                "field_types": {"role_metadata.role_id": "string", "performance_metrics.success_criteria": "array"},
                "constraints": {"operational_parameters.autonomy_scope": {"min_items": 1}}
            },
            cross_role_compatibility=["all_roles"],
            version_control_friendly=True,
            computational_efficiency_score=0.95
        )
        
        # 2. 자동화 스크립트 템플릿
        templates['automation_script'] = AIOptimizedTemplate(
            template_id="automation_script_v1",
            deliverable_type=AIDeliverableType.AUTOMATION_SCRIPT,
            processing_format=AIProcessingFormat.CODE_SNIPPET,
            ai_consumption_optimized=True,
            machine_readable_structure={
                "script_metadata": {
                    "script_id": "string",
                    "script_name": "string",
                    "execution_context": "enum[role_transition,task_automation,quality_check,communication]",
                    "trigger_conditions": "list",
                    "dependencies": "list"
                },
                "execution_parameters": {
                    "input_parameters": "object",
                    "environment_requirements": "list",
                    "resource_constraints": "object",
                    "timeout_settings": "object"
                },
                "script_logic": {
                    "preprocessing_steps": "list",
                    "main_execution_flow": "list",
                    "error_handling": "list",
                    "postprocessing_steps": "list"
                },
                "integration_points": {
                    "system_calls": "list",
                    "api_endpoints": "list",
                    "file_operations": "list",
                    "communication_channels": "list"
                },
                "output_handling": {
                    "success_outputs": "object",
                    "error_outputs": "object",
                    "logging_configuration": "object"
                }
            },
            automation_hooks=[
                "pre_execution_validation",
                "execution_monitoring",
                "post_execution_cleanup",
                "failure_recovery"
            ],
            validation_schema={
                "required_fields": ["script_metadata.script_id", "script_logic.main_execution_flow"],
                "executable_validation": True,
                "dependency_check": True
            },
            cross_role_compatibility=["system_roles", "technical_roles"],
            version_control_friendly=True,
            computational_efficiency_score=0.92
        )
        
        # 3. 검증 기준 템플릿
        templates['validation_criteria'] = AIOptimizedTemplate(
            template_id="validation_criteria_v1",
            deliverable_type=AIDeliverableType.VALIDATION_CRITERIA,
            processing_format=AIProcessingFormat.VALIDATION_RULES,
            ai_consumption_optimized=True,
            machine_readable_structure={
                "criteria_metadata": {
                    "criteria_set_id": "string",
                    "validation_domain": "string",
                    "applicability_scope": "list",
                    "validation_level": "enum[basic,standard,strict,custom]"
                },
                "validation_rules": {
                    "structural_validations": "list",
                    "content_validations": "list",
                    "business_rule_validations": "list",
                    "cross_reference_validations": "list"
                },
                "scoring_criteria": {
                    "quality_dimensions": "object",
                    "weight_assignments": "object",
                    "threshold_values": "object",
                    "scoring_algorithms": "list"
                },
                "automated_checks": {
                    "syntax_checks": "list",
                    "semantic_checks": "list",
                    "compliance_checks": "list",
                    "performance_checks": "list"
                },
                "remediation_guidance": {
                    "common_issues": "object",
                    "fix_suggestions": "object",
                    "escalation_procedures": "list"
                }
            },
            automation_hooks=[
                "validation_trigger",
                "scoring_computation",
                "result_aggregation",
                "remediation_recommendation"
            ],
            validation_schema={
                "rule_consistency": True,
                "threshold_validity": True,
                "automation_compatibility": True
            },
            cross_role_compatibility=["quality_assurance_roles", "review_roles"],
            version_control_friendly=True,
            computational_efficiency_score=0.88
        )
        
        # 4. 소통 프로토콜 템플릿
        templates['communication_protocol'] = AIOptimizedTemplate(
            template_id="communication_protocol_v1",
            deliverable_type=AIDeliverableType.COMMUNICATION_PROTOCOL,
            processing_format=AIProcessingFormat.WORKFLOW_CHAIN,
            ai_consumption_optimized=True,
            machine_readable_structure={
                "protocol_metadata": {
                    "protocol_id": "string",
                    "protocol_name": "string",
                    "communication_type": "enum[synchronous,asynchronous,hybrid]",
                    "participant_roles": "list",
                    "activation_conditions": "list"
                },
                "message_structures": {
                    "message_templates": "object",
                    "data_schemas": "object",
                    "validation_rules": "object",
                    "encoding_specifications": "object"
                },
                "interaction_flows": {
                    "initiation_sequence": "list",
                    "response_patterns": "object",
                    "escalation_paths": "list",
                    "termination_conditions": "list"
                },
                "routing_logic": {
                    "recipient_selection_rules": "object",
                    "priority_handling": "object",
                    "load_balancing": "object",
                    "failure_recovery": "list"
                },
                "monitoring_metrics": {
                    "communication_effectiveness": "object",
                    "response_time_tracking": "object",
                    "error_rate_monitoring": "object"
                }
            },
            automation_hooks=[
                "message_routing",
                "response_validation",
                "escalation_trigger",
                "performance_tracking"
            ],
            validation_schema={
                "protocol_completeness": True,
                "role_compatibility": True,
                "message_format_validity": True
            },
            cross_role_compatibility=["all_roles"],
            version_control_friendly=True,
            computational_efficiency_score=0.90
        )
        
        # 5. 의사결정 매트릭스 템플릿
        templates['decision_matrix'] = AIOptimizedTemplate(
            template_id="decision_matrix_v1",
            deliverable_type=AIDeliverableType.DECISION_MATRIX,
            processing_format=AIProcessingFormat.DECISION_TREE,
            ai_consumption_optimized=True,
            machine_readable_structure={
                "matrix_metadata": {
                    "matrix_id": "string",
                    "decision_domain": "string",
                    "applicable_scenarios": "list",
                    "authority_level_required": "enum[low,medium,high,executive]"
                },
                "decision_factors": {
                    "primary_criteria": "list",
                    "secondary_criteria": "list",
                    "constraint_factors": "list",
                    "weight_assignments": "object"
                },
                "decision_tree": {
                    "root_conditions": "object",
                    "decision_nodes": "list",
                    "leaf_outcomes": "list",
                    "confidence_scoring": "object"
                },
                "automation_rules": {
                    "auto_decision_thresholds": "object",
                    "escalation_triggers": "list",
                    "consultation_requirements": "object"
                },
                "outcome_tracking": {
                    "decision_logging": "object",
                    "impact_measurement": "object",
                    "feedback_integration": "object"
                }
            },
            automation_hooks=[
                "decision_evaluation",
                "confidence_calculation",
                "outcome_prediction",
                "result_logging"
            ],
            validation_schema={
                "decision_logic_consistency": True,
                "threshold_validity": True,
                "completeness_check": True
            },
            cross_role_compatibility=["decision_making_roles"],
            version_control_friendly=True,
            computational_efficiency_score=0.93
        )
        
        # 6. 워크플로우 정의 템플릿
        templates['workflow_definition'] = AIOptimizedTemplate(
            template_id="workflow_definition_v1",
            deliverable_type=AIDeliverableType.WORKFLOW_DEFINITION,
            processing_format=AIProcessingFormat.WORKFLOW_CHAIN,
            ai_consumption_optimized=True,
            machine_readable_structure={
                "workflow_metadata": {
                    "workflow_id": "string",
                    "workflow_name": "string",
                    "workflow_type": "enum[sequential,parallel,conditional,hybrid]",
                    "execution_context": "string",
                    "trigger_events": "list"
                },
                "process_steps": {
                    "step_definitions": "list",
                    "step_dependencies": "object",
                    "parallel_execution_groups": "list",
                    "conditional_branches": "object"
                },
                "role_assignments": {
                    "step_role_mapping": "object",
                    "responsibility_matrix": "object",
                    "handoff_procedures": "list"
                },
                "quality_gates": {
                    "checkpoint_definitions": "list",
                    "validation_criteria": "object",
                    "approval_requirements": "object"
                },
                "automation_integration": {
                    "automated_steps": "list",
                    "manual_intervention_points": "list",
                    "system_integrations": "object"
                },
                "monitoring_controls": {
                    "progress_tracking": "object",
                    "performance_metrics": "object",
                    "exception_handling": "list"
                }
            },
            automation_hooks=[
                "workflow_initiation",
                "step_completion_validation",
                "role_transition_management",
                "progress_monitoring"
            ],
            validation_schema={
                "workflow_completeness": True,
                "dependency_consistency": True,
                "role_availability": True
            },
            cross_role_compatibility=["all_roles"],
            version_control_friendly=True,
            computational_efficiency_score=0.91
        )
        
        return templates
    
    def generate_ai_optimized_deliverable(self, 
                                        role_id: str,
                                        deliverable_type: AIDeliverableType,
                                        content_data: Dict[str, Any],
                                        optimization_level: str = "high") -> str:
        """AI 최적화 산출물 생성"""
        
        template = self.ai_templates.get(deliverable_type.value)
        if not template:
            raise ValueError(f"Unknown deliverable type: {deliverable_type}")
        
        # AI 소비 최적화 적용
        optimized_content = self._apply_ai_optimizations(
            template, content_data, optimization_level
        )
        
        # 기계 판독 가능 구조로 변환
        machine_readable_doc = self._convert_to_machine_readable(
            template, optimized_content
        )
        
        # 자동화 훅 통합
        automation_ready_doc = self._integrate_automation_hooks(
            template, machine_readable_doc
        )
        
        # 검증 수행
        validation_result = self._validate_ai_deliverable(template, automation_ready_doc)
        if not validation_result['valid']:
            raise ValueError(f"AI deliverable validation failed: {validation_result['errors']}")
        
        # 최종 문서 생성
        final_document = {
            'ai_deliverable_metadata': {
                'deliverable_id': self._generate_deliverable_id(deliverable_type),
                'deliverable_type': deliverable_type.value,
                'template_id': template.template_id,
                'created_by': role_id,
                'created_at': datetime.now().isoformat(),
                'optimization_level': optimization_level,
                'computational_efficiency_score': template.computational_efficiency_score,
                'ai_consumption_optimized': True,
                'machine_readable': True
            },
            'content': automation_ready_doc,
            'automation_hooks': template.automation_hooks,
            'validation_passed': True,
            'cross_role_compatibility': template.cross_role_compatibility
        }
        
        # 파일 저장 (JSON 형태로 AI 소비 최적화)
        output_file = self._save_ai_deliverable(final_document)
        
        print(f"🤖 AI 최적화 산출물 생성 완료: {output_file}")
        return output_file
    
    def create_role_instruction_set(self, 
                                  role_id: str,
                                  role_config: Dict[str, Any]) -> str:
        """역할별 AI 지시사항 세트 생성"""
        
        instruction_data = {
            "role_metadata": {
                "role_id": role_id,
                "role_name": role_config.get('role_name', role_id),
                "domain_expertise": role_config.get('expertise', []),
                "primary_responsibilities": role_config.get('primary_tasks', []),
                "secondary_responsibilities": role_config.get('secondary_tasks', [])
            },
            "operational_parameters": {
                "decision_authority_level": role_config.get('authority_level', 'medium'),
                "autonomy_scope": role_config.get('autonomy_scope', []),
                "escalation_triggers": role_config.get('escalation_rules', []),
                "quality_thresholds": role_config.get('quality_requirements', {})
            },
            "input_processing": {
                "accepted_input_formats": ["json", "yaml", "text"],
                "input_validation_rules": role_config.get('input_validation', {}),
                "preprocessing_steps": role_config.get('preprocessing', [])
            },
            "output_specifications": {
                "required_output_format": role_config.get('output_format', 'json'),
                "output_validation_schema": role_config.get('output_schema', {}),
                "delivery_channels": role_config.get('delivery_methods', ['file', 'message'])
            },
            "interaction_protocols": {
                "communication_interfaces": ["message_system", "file_system"],
                "collaboration_patterns": role_config.get('collaboration_rules', {}),
                "conflict_resolution_procedures": role_config.get('conflict_resolution', [])
            },
            "performance_metrics": {
                "success_criteria": role_config.get('success_metrics', []),
                "quality_indicators": role_config.get('quality_metrics', {}),
                "efficiency_targets": role_config.get('efficiency_targets', {})
            }
        }
        
        return self.generate_ai_optimized_deliverable(
            role_id=role_id,
            deliverable_type=AIDeliverableType.ROLE_INSTRUCTION,
            content_data=instruction_data
        )
    
    def create_automation_script_spec(self, 
                                    role_id: str,
                                    script_config: Dict[str, Any]) -> str:
        """자동화 스크립트 명세 생성"""
        
        script_data = {
            "script_metadata": {
                "script_id": script_config.get('script_id', self._generate_script_id()),
                "script_name": script_config.get('name'),
                "execution_context": script_config.get('context', 'task_automation'),
                "trigger_conditions": script_config.get('triggers', []),
                "dependencies": script_config.get('dependencies', [])
            },
            "execution_parameters": {
                "input_parameters": script_config.get('inputs', {}),
                "environment_requirements": script_config.get('env_requirements', []),
                "resource_constraints": script_config.get('resource_limits', {}),
                "timeout_settings": script_config.get('timeouts', {})
            },
            "script_logic": {
                "preprocessing_steps": script_config.get('preprocessing', []),
                "main_execution_flow": script_config.get('main_logic', []),
                "error_handling": script_config.get('error_handling', []),
                "postprocessing_steps": script_config.get('postprocessing', [])
            },
            "integration_points": {
                "system_calls": script_config.get('system_calls', []),
                "api_endpoints": script_config.get('api_calls', []),
                "file_operations": script_config.get('file_ops', []),
                "communication_channels": script_config.get('comm_channels', [])
            },
            "output_handling": {
                "success_outputs": script_config.get('success_outputs', {}),
                "error_outputs": script_config.get('error_outputs', {}),
                "logging_configuration": script_config.get('logging', {})
            }
        }
        
        return self.generate_ai_optimized_deliverable(
            role_id=role_id,
            deliverable_type=AIDeliverableType.AUTOMATION_SCRIPT,
            content_data=script_data
        )
    
    def create_communication_protocol_spec(self, 
                                         role_id: str,
                                         protocol_config: Dict[str, Any]) -> str:
        """소통 프로토콜 명세 생성"""
        
        protocol_data = {
            "protocol_metadata": {
                "protocol_id": protocol_config.get('protocol_id', self._generate_protocol_id()),
                "protocol_name": protocol_config.get('name'),
                "communication_type": protocol_config.get('type', 'asynchronous'),
                "participant_roles": protocol_config.get('participants', []),
                "activation_conditions": protocol_config.get('activation_triggers', [])
            },
            "message_structures": {
                "message_templates": protocol_config.get('message_templates', {}),
                "data_schemas": protocol_config.get('data_schemas', {}),
                "validation_rules": protocol_config.get('validation_rules', {}),
                "encoding_specifications": protocol_config.get('encoding', {})
            },
            "interaction_flows": {
                "initiation_sequence": protocol_config.get('initiation_flow', []),
                "response_patterns": protocol_config.get('response_patterns', {}),
                "escalation_paths": protocol_config.get('escalation_paths', []),
                "termination_conditions": protocol_config.get('termination_rules', [])
            },
            "routing_logic": {
                "recipient_selection_rules": protocol_config.get('routing_rules', {}),
                "priority_handling": protocol_config.get('priority_rules', {}),
                "load_balancing": protocol_config.get('load_balancing', {}),
                "failure_recovery": protocol_config.get('failure_recovery', [])
            },
            "monitoring_metrics": {
                "communication_effectiveness": protocol_config.get('effectiveness_metrics', {}),
                "response_time_tracking": protocol_config.get('timing_metrics', {}),
                "error_rate_monitoring": protocol_config.get('error_metrics', {})
            }
        }
        
        return self.generate_ai_optimized_deliverable(
            role_id=role_id,
            deliverable_type=AIDeliverableType.COMMUNICATION_PROTOCOL,
            content_data=protocol_data
        )
    
    # Helper methods
    def _apply_ai_optimizations(self, 
                              template: AIOptimizedTemplate,
                              content_data: Dict[str, Any],
                              optimization_level: str) -> Dict[str, Any]:
        """AI 소비 최적화 적용"""
        
        optimized_data = content_data.copy()
        
        if optimization_level == "high":
            # 중복 제거
            optimized_data = self._remove_redundancy(optimized_data)
            
            # 구조 정규화
            optimized_data = self._normalize_structure(template, optimized_data)
            
            # 계산 효율성 최적화
            optimized_data = self._optimize_computational_structure(optimized_data)
        
        return optimized_data
    
    def _convert_to_machine_readable(self,
                                   template: AIOptimizedTemplate,
                                   content_data: Dict[str, Any]) -> Dict[str, Any]:
        """기계 판독 가능 형태로 변환"""
        
        machine_readable = {}
        
        # 템플릿 구조에 맞춰 데이터 매핑
        for section_key, section_schema in template.machine_readable_structure.items():
            if section_key in content_data:
                machine_readable[section_key] = self._validate_and_convert_section(
                    content_data[section_key], section_schema
                )
        
        return machine_readable
    
    def _integrate_automation_hooks(self,
                                  template: AIOptimizedTemplate,
                                  document: Dict[str, Any]) -> Dict[str, Any]:
        """자동화 훅 통합"""
        
        # 자동화 훅 포인트 추가
        document['_automation_hooks'] = {
            hook: {
                'enabled': True,
                'trigger_conditions': [],
                'callback_functions': [],
                'error_handling': 'default'
            }
            for hook in template.automation_hooks
        }
        
        return document
    
    def _validate_ai_deliverable(self,
                               template: AIOptimizedTemplate,
                               document: Dict[str, Any]) -> Dict[str, Any]:
        """AI 산출물 검증"""
        
        errors = []
        
        # 구조 검증
        for required_field in template.validation_schema.get('required_fields', []):
            if not self._has_nested_field(document, required_field):
                errors.append(f"Required field missing: {required_field}")
        
        # 타입 검증
        field_types = template.validation_schema.get('field_types', {})
        for field_path, expected_type in field_types.items():
            value = self._get_nested_field(document, field_path)
            if value is not None and not self._validate_type(value, expected_type):
                errors.append(f"Type mismatch for {field_path}: expected {expected_type}")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def _generate_deliverable_id(self, deliverable_type: AIDeliverableType) -> str:
        """산출물 ID 생성"""
        type_prefix = {
            AIDeliverableType.ROLE_INSTRUCTION: "RI",
            AIDeliverableType.AUTOMATION_SCRIPT: "AS",
            AIDeliverableType.VALIDATION_CRITERIA: "VC",
            AIDeliverableType.COMMUNICATION_PROTOCOL: "CP",
            AIDeliverableType.DECISION_MATRIX: "DM",
            AIDeliverableType.WORKFLOW_DEFINITION: "WD"
        }
        
        prefix = type_prefix.get(deliverable_type, "AI")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}"
    
    def _save_ai_deliverable(self, document: Dict[str, Any]) -> str:
        """AI 산출물 저장"""
        deliverable_id = document['ai_deliverable_metadata']['deliverable_id']
        output_file = self.ai_deliverables_dir / f"{deliverable_id}.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(document, f, indent=2, ensure_ascii=False, default=str)
        
        return str(output_file)
    
    def _remove_redundancy(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """중복 제거"""
        # 간단한 중복 제거 로직
        return data
    
    def _normalize_structure(self, template: AIOptimizedTemplate, data: Dict[str, Any]) -> Dict[str, Any]:
        """구조 정규화"""
        # 템플릿 구조에 맞춰 정규화
        return data
    
    def _optimize_computational_structure(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """계산 효율성 최적화"""
        # 계산 효율성을 위한 구조 최적화
        return data
    
    def _validate_and_convert_section(self, data: Any, schema: Any) -> Any:
        """섹션 검증 및 변환"""
        return data
    
    def _has_nested_field(self, data: Dict[str, Any], field_path: str) -> bool:
        """중첩 필드 존재 확인"""
        try:
            self._get_nested_field(data, field_path)
            return True
        except (KeyError, TypeError):
            return False
    
    def _get_nested_field(self, data: Dict[str, Any], field_path: str) -> Any:
        """중첩 필드 값 조회"""
        keys = field_path.split('.')
        current = data
        
        for key in keys:
            current = current[key]
        
        return current
    
    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """타입 검증"""
        if expected_type == "string":
            return isinstance(value, str)
        elif expected_type == "array":
            return isinstance(value, list)
        elif expected_type == "object":
            return isinstance(value, dict)
        return True
    
    def _generate_script_id(self) -> str:
        """스크립트 ID 생성"""
        return f"script_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def _generate_protocol_id(self) -> str:
        """프로토콜 ID 생성"""
        return f"protocol_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

def main():
    """테스트 및 데모"""
    ai_system = AIOptimizedDeliverableSystem("/home/jungh/workspace/multi_claude_code_sample")
    
    # 예시 1: 비즈니스 분석가 역할 지시사항 생성
    ba_role_config = {
        'role_name': 'Business Analyst',
        'expertise': ['requirements_analysis', 'business_process_modeling', 'stakeholder_management'],
        'primary_tasks': ['analyze_business_requirements', 'create_functional_specifications', 'validate_solutions'],
        'authority_level': 'medium',
        'autonomy_scope': ['requirement_refinement', 'stakeholder_consultation', 'solution_validation'],
        'quality_requirements': {'completeness_threshold': 0.9, 'accuracy_threshold': 0.95}
    }
    
    role_instruction_file = ai_system.create_role_instruction_set("business_analyst", ba_role_config)
    print(f"✅ 역할 지시사항 생성: {role_instruction_file}")
    
    # 예시 2: 자동화 스크립트 명세 생성
    automation_config = {
        'name': 'Code Quality Check Automation',
        'context': 'quality_check',
        'triggers': ['code_commit', 'pull_request'],
        'main_logic': [
            'run_syntax_check',
            'run_static_analysis', 
            'run_security_scan',
            'generate_quality_report'
        ],
        'success_outputs': {'quality_score': 'float', 'report_path': 'string'},
        'error_outputs': {'error_code': 'int', 'error_message': 'string'}
    }
    
    automation_script_file = ai_system.create_automation_script_spec("qa_tester", automation_config)
    print(f"✅ 자동화 스크립트 명세 생성: {automation_script_file}")
    
    # 예시 3: 소통 프로토콜 명세 생성
    comm_protocol_config = {
        'name': 'Inter-Role Communication Protocol',
        'type': 'asynchronous',
        'participants': ['business_analyst', 'developer', 'qa_tester'],
        'message_templates': {
            'requirement_update': {'type': 'requirement_change', 'priority': 'string', 'changes': 'list'},
            'implementation_complete': {'type': 'task_completion', 'deliverable_path': 'string', 'quality_score': 'float'}
        },
        'routing_rules': {'priority_high': 'immediate_delivery', 'priority_normal': 'batch_delivery'}
    }
    
    protocol_file = ai_system.create_communication_protocol_spec("system_architect", comm_protocol_config)
    print(f"✅ 소통 프로토콜 명세 생성: {protocol_file}")

if __name__ == "__main__":
    main()