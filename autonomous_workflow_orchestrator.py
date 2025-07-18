#!/usr/bin/env python3
"""
Autonomous Workflow Orchestrator for Multi-Agent Claude Code
완전 자율 워크플로우 오케스트레이터 - 사용자 상호작용 및 요구사항 협의 자동화
"""

import os
import json
import yaml
import asyncio
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import subprocess

# 다른 시스템들 import
from seamless_role_transition_system import SeamlessTransitionEngine
from enhanced_communication_system import ActiveCommunicationEngine, SmartMessage, MessageType
from intelligent_review_system import IntelligentReviewEngine, ReviewType

class InteractionType(Enum):
    REQUIREMENT_CLARIFICATION = "requirement_clarification"
    PROGRESS_UPDATE = "progress_update"
    DECISION_REQUEST = "decision_request"
    APPROVAL_REQUEST = "approval_request"
    ISSUE_ESCALATION = "issue_escalation"
    FINAL_DELIVERY = "final_delivery"

class UserRole(Enum):
    PRODUCT_OWNER = "product_owner"
    STAKEHOLDER = "stakeholder"
    PROJECT_SPONSOR = "project_sponsor"
    END_USER = "end_user"

@dataclass
class RequirementNegotiation:
    """요구사항 협상"""
    negotiation_id: str
    topic: str
    current_proposal: Dict[str, Any]
    stakeholder_feedback: List[Dict[str, Any]]
    ai_recommendations: List[str]
    status: str  # "active", "resolved", "escalated"
    priority: str
    deadline: datetime

@dataclass
class UserInteraction:
    """사용자 상호작용"""
    interaction_id: str
    interaction_type: InteractionType
    user_role: UserRole
    context: Dict[str, Any]
    ai_query: str
    user_response: Optional[str]
    ai_follow_up: Optional[str]
    status: str  # "pending", "completed", "timeout"
    created_at: datetime
    resolved_at: Optional[datetime]

class AutonomousWorkflowOrchestrator:
    """자율 워크플로우 오케스트레이터"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.orchestrator_dir = self.project_root / "orchestrator"
        self.interactions_dir = self.orchestrator_dir / "interactions"
        self.negotiations_dir = self.orchestrator_dir / "negotiations"
        
        # 디렉토리 생성
        self.orchestrator_dir.mkdir(exist_ok=True)
        self.interactions_dir.mkdir(exist_ok=True)
        self.negotiations_dir.mkdir(exist_ok=True)
        
        # 다른 시스템들 초기화
        self.transition_engine = SeamlessTransitionEngine(str(project_root))
        self.communication_engine = ActiveCommunicationEngine(str(project_root))
        self.review_engine = IntelligentReviewEngine(str(project_root))
        
        # 상태 관리
        self.active_interactions: Dict[str, UserInteraction] = {}
        self.active_negotiations: Dict[str, RequirementNegotiation] = {}
        self.project_context: Dict[str, Any] = {}
        self.user_preferences: Dict[str, Any] = {}
        
        # 자율 설정
        self.auto_approval_thresholds = {
            "low_risk_changes": 0.8,
            "documentation_updates": 0.9,
            "minor_improvements": 0.85
        }
        
        # 백그라운드 작업
        self.orchestration_active = True
        self.orchestration_thread = threading.Thread(target=self._orchestration_loop, daemon=True)
        self.interaction_handler = threading.Thread(target=self._handle_user_interactions, daemon=True)
        
        # 초기화
        self._load_project_context()
        self._load_user_preferences()
        
        # 스레드 시작
        self.orchestration_thread.start()
        self.interaction_handler.start()
        
        print("🎼 Autonomous Workflow Orchestrator 시작됨")
    
    def start_fully_autonomous_project(self, 
                                     initial_brief: Dict[str, Any],
                                     user_contact_info: Dict[str, Any] = None,
                                     autonomy_level: str = "high") -> str:
        """완전 자율 프로젝트 시작"""
        
        print("🚀 완전 자율 프로젝트 시작")
        
        # 프로젝트 ID 생성
        project_id = f"auto_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 초기 요구사항 분석 및 정제
        refined_requirements = self._analyze_and_refine_initial_brief(initial_brief)
        
        # 프로젝트 컨텍스트 설정
        self.project_context = {
            'project_id': project_id,
            'start_time': datetime.now().isoformat(),
            'initial_brief': initial_brief,
            'refined_requirements': refined_requirements,
            'user_contact': user_contact_info,
            'autonomy_level': autonomy_level,
            'auto_decisions_made': [],
            'user_consultations': [],
            'milestone_approvals': []
        }
        
        # 자동 프로젝트 계획 수립
        project_plan = self._generate_autonomous_project_plan(refined_requirements)
        
        # 사용자와의 초기 협의 (필요한 경우만)
        if autonomy_level in ["medium", "low"]:
            consultation_needed = self._assess_consultation_needs(project_plan)
            if consultation_needed:
                self._initiate_user_consultation(consultation_needed)
        
        # 자율 워크플로우 시작
        workflow_success = self.transition_engine.start_autonomous_workflow(
            initial_role="project_manager",
            project_config=self.project_context
        )
        
        if workflow_success:
            # 자동 모니터링 설정
            self._setup_autonomous_monitoring(project_id)
            
            # 초기 상태 저장
            self._save_project_state()
            
            print(f"✅ 자율 프로젝트 {project_id} 시작 완료")
            return project_id
        else:
            raise Exception("자율 워크플로우 시작 실패")
    
    def _analyze_and_refine_initial_brief(self, initial_brief: Dict[str, Any]) -> Dict[str, Any]:
        """초기 브리프 분석 및 정제"""
        
        # 핵심 정보 추출
        project_name = initial_brief.get('project_name', 'Unnamed Project')
        description = initial_brief.get('description', '')
        features = initial_brief.get('features', [])
        constraints = initial_brief.get('constraints', {})
        
        # AI 기반 요구사항 분석
        refined_requirements = {
            'project_name': project_name,
            'business_objective': self._extract_business_objective(description),
            'core_features': self._prioritize_features(features),
            'technical_constraints': constraints.get('technical', {}),
            'timeline_constraints': constraints.get('timeline', {}),
            'budget_constraints': constraints.get('budget', {}),
            'quality_requirements': self._infer_quality_requirements(description, features),
            'stakeholders': self._identify_stakeholders(initial_brief),
            'success_criteria': self._generate_success_criteria(description, features),
            'risk_factors': self._identify_initial_risks(initial_brief)
        }
        
        # 누락된 중요 정보 식별
        missing_info = self._identify_missing_critical_info(refined_requirements)
        if missing_info:
            refined_requirements['missing_info'] = missing_info
            refined_requirements['requires_user_input'] = True
        
        return refined_requirements
    
    def _generate_autonomous_project_plan(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """자율적 프로젝트 계획 생성"""
        
        # 기능 기반 작업 분해
        work_breakdown = self._create_intelligent_wbs(requirements['core_features'])
        
        # 자동 일정 계산
        timeline = self._calculate_optimal_timeline(work_breakdown, requirements.get('timeline_constraints', {}))
        
        # 리소스 요구사항 자동 계산
        resource_requirements = self._calculate_resource_requirements(work_breakdown)
        
        # 위험 기반 완충 시간 계산
        risk_buffers = self._calculate_risk_buffers(requirements['risk_factors'], timeline)
        
        project_plan = {
            'work_breakdown_structure': work_breakdown,
            'timeline': timeline,
            'resource_requirements': resource_requirements,
            'risk_mitigation': risk_buffers,
            'quality_gates': self._define_quality_gates(requirements),
            'dependencies': self._map_dependencies(work_breakdown),
            'communication_plan': self._create_communication_plan(requirements['stakeholders']),
            'auto_decision_rules': self._create_auto_decision_rules(requirements)
        }
        
        return project_plan
    
    def _assess_consultation_needs(self, project_plan: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """사용자 협의 필요성 평가"""
        
        consultation_triggers = []
        
        # 높은 리스크 요소
        high_risk_items = [item for item in project_plan.get('risk_mitigation', {}).values() 
                          if isinstance(item, dict) and item.get('severity', 'low') == 'high']
        
        if high_risk_items:
            consultation_triggers.append({
                'type': 'high_risk_approval',
                'items': high_risk_items,
                'reason': '높은 리스크 요소에 대한 승인 필요'
            })
        
        # 예산 초과 가능성
        estimated_cost = project_plan.get('resource_requirements', {}).get('estimated_cost', 0)
        if estimated_cost > self.user_preferences.get('budget_alert_threshold', 50000):
            consultation_triggers.append({
                'type': 'budget_approval',
                'estimated_cost': estimated_cost,
                'reason': '예상 비용이 임계값 초과'
            })
        
        # 일정 지연 가능성
        estimated_duration = project_plan.get('timeline', {}).get('total_duration_days', 0)
        if estimated_duration > self.user_preferences.get('timeline_alert_threshold', 30):
            consultation_triggers.append({
                'type': 'timeline_approval',
                'estimated_duration': estimated_duration,
                'reason': '예상 기간이 임계값 초과'
            })
        
        if consultation_triggers:
            return {
                'consultation_type': 'project_approval',
                'triggers': consultation_triggers,
                'recommended_action': 'user_review_required'
            }
        
        return None
    
    def _initiate_user_consultation(self, consultation_needs: Dict[str, Any]):
        """사용자 협의 시작"""
        
        interaction_id = f"consult_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 협의 내용 생성
        consultation_message = self._generate_consultation_message(consultation_needs)
        
        # 사용자 상호작용 생성
        interaction = UserInteraction(
            interaction_id=interaction_id,
            interaction_type=InteractionType.DECISION_REQUEST,
            user_role=UserRole.PRODUCT_OWNER,
            context=consultation_needs,
            ai_query=consultation_message,
            user_response=None,
            ai_follow_up=None,
            status="pending",
            created_at=datetime.now(),
            resolved_at=None
        )
        
        self.active_interactions[interaction_id] = interaction
        self._save_interaction(interaction)
        
        # 사용자에게 알림 전송
        self._send_user_notification(interaction)
        
        print(f"👤 사용자 협의 시작: {interaction_id}")
    
    def handle_autonomous_decision_making(self, 
                                        decision_context: Dict[str, Any],
                                        confidence_level: float) -> Dict[str, Any]:
        """자율적 의사결정 처리"""
        
        decision_type = decision_context.get('type', 'general')
        
        # 자동 결정 가능 여부 확인
        auto_decision_threshold = self.auto_approval_thresholds.get(decision_type, 0.7)
        
        if confidence_level >= auto_decision_threshold:
            # 자동 결정
            decision = self._make_autonomous_decision(decision_context)
            
            # 결정 기록
            self.project_context['auto_decisions_made'].append({
                'timestamp': datetime.now().isoformat(),
                'context': decision_context,
                'decision': decision,
                'confidence': confidence_level,
                'rationale': decision.get('rationale', '')
            })
            
            print(f"🤖 자동 결정: {decision_type} (신뢰도: {confidence_level:.2f})")
            return decision
        
        else:
            # 사용자 협의 필요
            consultation_id = self._escalate_to_user_decision(decision_context, confidence_level)
            
            return {
                'status': 'escalated',
                'consultation_id': consultation_id,
                'reason': f'신뢰도 {confidence_level:.2f}가 임계값 {auto_decision_threshold} 미만'
            }
    
    def _make_autonomous_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """자율적 결정 수행"""
        
        decision_type = context.get('type')
        
        if decision_type == 'technical_approach':
            return self._decide_technical_approach(context)
        elif decision_type == 'feature_prioritization':
            return self._decide_feature_priority(context)
        elif decision_type == 'resource_allocation':
            return self._decide_resource_allocation(context)
        elif decision_type == 'quality_trade_off':
            return self._decide_quality_trade_off(context)
        else:
            return self._decide_general_issue(context)
    
    def _decide_technical_approach(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """기술적 접근법 결정"""
        
        options = context.get('options', [])
        criteria = context.get('criteria', {})
        
        # 기술 스택 호환성, 성능, 유지보수성 등을 종합 평가
        scored_options = []
        
        for option in options:
            score = 0.0
            
            # 성능 점수
            if option.get('performance_rating', 0) > 8:
                score += 0.3
            
            # 유지보수성 점수
            if option.get('maintainability', 'medium') == 'high':
                score += 0.25
            
            # 팀 숙련도 점수
            if option.get('team_familiarity', 'medium') == 'high':
                score += 0.2
            
            # 커뮤니티 지원 점수
            if option.get('community_support', 'medium') == 'high':
                score += 0.15
            
            # 비용 점수
            if option.get('cost_rating', 'medium') == 'low':
                score += 0.1
            
            scored_options.append({
                'option': option,
                'score': score
            })
        
        # 최고 점수 옵션 선택
        best_option = max(scored_options, key=lambda x: x['score'])
        
        return {
            'status': 'decided',
            'selected_option': best_option['option'],
            'score': best_option['score'],
            'rationale': f"종합 점수 {best_option['score']:.2f}로 최적 옵션 선택",
            'alternative_options': [opt for opt in scored_options if opt != best_option]
        }
    
    def _decide_feature_priority(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """기능 우선순위 결정"""
        
        features = context.get('features', [])
        
        # 비즈니스 가치, 구현 복잡도, 사용자 영향도 기반 우선순위 계산
        prioritized_features = []
        
        for feature in features:
            business_value = feature.get('business_value', 5)  # 1-10
            complexity = feature.get('complexity', 5)  # 1-10 (낮을수록 좋음)
            user_impact = feature.get('user_impact', 5)  # 1-10
            
            # 우선순위 점수 계산 (가치와 영향도는 높을수록, 복잡도는 낮을수록 좋음)
            priority_score = (business_value * 0.4) + (user_impact * 0.4) + ((11 - complexity) * 0.2)
            
            prioritized_features.append({
                'feature': feature,
                'priority_score': priority_score,
                'priority_level': self._classify_priority(priority_score)
            })
        
        # 점수 순으로 정렬
        prioritized_features.sort(key=lambda x: x['priority_score'], reverse=True)
        
        return {
            'status': 'decided',
            'prioritized_features': prioritized_features,
            'rationale': '비즈니스 가치, 사용자 영향도, 구현 복잡도를 종합 고려'
        }
    
    def _orchestration_loop(self):
        """오케스트레이션 메인 루프"""
        
        while self.orchestration_active:
            try:
                # 프로젝트 진행 상황 모니터링
                self._monitor_project_progress()
                
                # 자동 품질 검증
                self._perform_automatic_quality_checks()
                
                # 사용자 상호작용 타임아웃 처리
                self._handle_interaction_timeouts()
                
                # 자동 승인 처리
                self._process_automatic_approvals()
                
                # 프로젝트 상태 업데이트
                self._update_project_status()
                
                time.sleep(30)  # 30초마다 실행
                
            except Exception as e:
                print(f"⚠️ 오케스트레이션 오류: {str(e)}")
                time.sleep(60)
    
    def _monitor_project_progress(self):
        """프로젝트 진행 상황 모니터링"""
        
        # 전체 진행률 확인
        overall_progress = self.transition_engine.calculate_overall_progress()
        
        # 예상 완료 시간 계산
        estimated_completion = self._calculate_estimated_completion()
        
        # 지연 위험 평가
        delay_risk = self._assess_delay_risk()
        
        # 사용자 알림 필요성 판단
        if delay_risk > 0.7:  # 70% 이상 지연 위험
            self._create_progress_alert(delay_risk, estimated_completion)
        
        # 마일스톤 달성 확인
        achieved_milestones = self._check_milestone_achievements()
        for milestone in achieved_milestones:
            self._celebrate_milestone_achievement(milestone)
    
    def _perform_automatic_quality_checks(self):
        """자동 품질 검증"""
        
        # 새로운 산출물 확인
        new_deliverables = self._scan_for_new_deliverables()
        
        for deliverable in new_deliverables:
            # 자동 리뷰 트리거
            review_type = self._determine_review_type(deliverable)
            
            try:
                review_id = self.review_engine.request_review(
                    deliverable_path=deliverable['path'],
                    reviewee_role=deliverable['author'],
                    review_type=review_type
                )
                
                # 리뷰 수행
                review_result = self.review_engine.conduct_intelligent_review(review_id)
                
                # 결과에 따른 자동 처리
                self._handle_review_result(review_result)
                
            except Exception as e:
                print(f"⚠️ 자동 품질 검증 오류 ({deliverable['path']}): {str(e)}")
    
    def _handle_user_interactions(self):
        """사용자 상호작용 처리"""
        
        while self.orchestration_active:
            try:
                # 대기 중인 상호작용 확인
                pending_interactions = [
                    interaction for interaction in self.active_interactions.values()
                    if interaction.status == "pending"
                ]
                
                for interaction in pending_interactions:
                    # 사용자 응답 확인
                    user_response = self._check_user_response(interaction.interaction_id)
                    
                    if user_response:
                        # 응답 처리
                        self._process_user_response(interaction, user_response)
                    
                    # 타임아웃 확인
                    elif self._is_interaction_timeout(interaction):
                        self._handle_interaction_timeout(interaction)
                
                time.sleep(15)  # 15초마다 확인
                
            except Exception as e:
                print(f"⚠️ 사용자 상호작용 처리 오류: {str(e)}")
                time.sleep(30)
    
    def provide_final_delivery_summary(self) -> Dict[str, Any]:
        """최종 전달 요약 생성"""
        
        # 프로젝트 완료 상태 확인
        completion_status = self._assess_project_completion()
        
        if completion_status['completion_percentage'] < 100:
            return {
                'status': 'incomplete',
                'completion_percentage': completion_status['completion_percentage'],
                'remaining_tasks': completion_status['remaining_tasks']
            }
        
        # 최종 산출물 수집
        all_deliverables = self._collect_all_deliverables()
        
        # 품질 보고서 생성
        quality_report = self._generate_quality_report()
        
        # 프로젝트 메트릭 수집
        project_metrics = self._collect_project_metrics()
        
        # 사용자 인수인계 자료 생성
        handover_package = self._create_handover_package()
        
        final_summary = {
            'project_id': self.project_context.get('project_id'),
            'completion_date': datetime.now().isoformat(),
            'total_duration': self._calculate_total_duration(),
            'deliverables': all_deliverables,
            'quality_report': quality_report,
            'project_metrics': project_metrics,
            'handover_package': handover_package,
            'auto_decisions_made': len(self.project_context.get('auto_decisions_made', [])),
            'user_consultations': len(self.project_context.get('user_consultations', [])),
            'success_criteria_met': self._verify_success_criteria(),
            'recommendations': self._generate_future_recommendations()
        }
        
        # 최종 사용자 알림
        self._send_final_delivery_notification(final_summary)
        
        return final_summary
    
    # Helper methods implementation
    def _extract_business_objective(self, description: str) -> str:
        """비즈니스 목표 추출"""
        # 간단한 키워드 기반 분석 (실제로는 더 정교한 NLP 필요)
        if "커뮤니티" in description:
            return "온라인 커뮤니티 플랫폼 구축을 통한 사용자 참여도 증대"
        elif "ecommerce" in description.lower():
            return "전자상거래 플랫폼을 통한 온라인 매출 증대"
        else:
            return "디지털 솔루션을 통한 비즈니스 프로세스 개선"
    
    def _prioritize_features(self, features: List[str]) -> List[Dict[str, Any]]:
        """기능 우선순위화"""
        prioritized = []
        
        for i, feature in enumerate(features):
            # 기본 우선순위 할당
            if i < len(features) // 3:
                priority = "high"
            elif i < 2 * len(features) // 3:
                priority = "medium"
            else:
                priority = "low"
            
            prioritized.append({
                'name': feature,
                'priority': priority,
                'estimated_effort': self._estimate_effort(feature),
                'business_value': self._estimate_business_value(feature)
            })
        
        return prioritized
    
    def _estimate_effort(self, feature: str) -> str:
        """개발 노력 추정"""
        if any(word in feature.lower() for word in ["authentication", "인증", "security", "보안"]):
            return "high"
        elif any(word in feature.lower() for word in ["crud", "basic", "simple", "기본"]):
            return "low"
        else:
            return "medium"
    
    def _estimate_business_value(self, feature: str) -> str:
        """비즈니스 가치 추정"""
        high_value_keywords = ["user", "customer", "revenue", "core", "main", "사용자", "핵심"]
        if any(keyword in feature.lower() for keyword in high_value_keywords):
            return "high"
        else:
            return "medium"
    
    def _infer_quality_requirements(self, description: str, features: List[str]) -> Dict[str, Any]:
        """품질 요구사항 추론"""
        return {
            'performance': {
                'response_time': '3초 이내',
                'concurrent_users': 1000,
                'availability': '99.9%'
            },
            'security': {
                'authentication': 'required',
                'data_encryption': 'required',
                'access_control': 'role_based'
            },
            'usability': {
                'mobile_responsive': True,
                'accessibility': 'WCAG_2.1',
                'browser_support': ['Chrome', 'Firefox', 'Safari', 'Edge']
            }
        }
    
    def _load_project_context(self):
        """프로젝트 컨텍스트 로드"""
        context_file = self.orchestrator_dir / "project_context.json"
        if context_file.exists():
            with open(context_file, 'r', encoding='utf-8') as f:
                self.project_context = json.load(f)
    
    def _load_user_preferences(self):
        """사용자 선호설정 로드"""
        prefs_file = self.orchestrator_dir / "user_preferences.json"
        if prefs_file.exists():
            with open(prefs_file, 'r', encoding='utf-8') as f:
                self.user_preferences = json.load(f)
        else:
            # 기본 설정
            self.user_preferences = {
                'budget_alert_threshold': 50000,
                'timeline_alert_threshold': 30,
                'quality_threshold': 0.8,
                'auto_approval_enabled': True,
                'notification_preferences': {
                    'email': True,
                    'slack': False,
                    'dashboard': True
                }
            }
    
    def _save_project_state(self):
        """프로젝트 상태 저장"""
        # 프로젝트 컨텍스트 저장
        context_file = self.orchestrator_dir / "project_context.json"
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(self.project_context, f, indent=2, ensure_ascii=False, default=str)
        
        # 상호작용 저장
        for interaction in self.active_interactions.values():
            self._save_interaction(interaction)
    
    def _save_interaction(self, interaction: UserInteraction):
        """상호작용 저장"""
        interaction_file = self.interactions_dir / f"{interaction.interaction_id}.json"
        
        # dataclass를 dict로 변환
        interaction_dict = asdict(interaction)
        interaction_dict['interaction_type'] = interaction.interaction_type.value
        interaction_dict['user_role'] = interaction.user_role.value
        
        with open(interaction_file, 'w', encoding='utf-8') as f:
            json.dump(interaction_dict, f, indent=2, ensure_ascii=False, default=str)

def main():
    """테스트 및 데모"""
    orchestrator = AutonomousWorkflowOrchestrator("/home/jungh/workspace/web_community_project")
    
    # 예시: 완전 자율 프로젝트 시작
    initial_brief = {
        'project_name': 'Community Platform Enhanced',
        'description': '사용자 간 소통을 위한 웹 커뮤니티 플랫폼 구축',
        'features': [
            '사용자 인증 시스템',
            '게시판 기능',
            '댓글 시스템',
            '실시간 알림',
            '모바일 지원'
        ],
        'constraints': {
            'timeline': {'max_duration_days': 7},
            'technical': {'stack': 'React + Node.js + PostgreSQL'},
            'budget': {'max_amount': 30000}
        }
    }
    
    user_contact = {
        'email': 'user@example.com',
        'preferred_communication': 'email',
        'timezone': 'Asia/Seoul'
    }
    
    project_id = orchestrator.start_fully_autonomous_project(
        initial_brief=initial_brief,
        user_contact_info=user_contact,
        autonomy_level="high"
    )
    
    print(f"✅ 자율 프로젝트 시작: {project_id}")

if __name__ == "__main__":
    main()