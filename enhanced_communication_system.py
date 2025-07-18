#!/usr/bin/env python3
"""
Enhanced Communication System for Multi-Agent Claude Code
능동적 소통과 지능적 협업을 위한 개선된 커뮤니케이션 시스템
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

class MessageType(Enum):
    QUESTION = "question"
    CLARIFICATION_REQUEST = "clarification_request"
    FEEDBACK_REQUEST = "feedback_request"
    COLLABORATION_PROPOSAL = "collaboration_proposal"
    REVIEW_REQUEST = "review_request"
    CONCERN_REPORT = "concern_report"
    KNOWLEDGE_SHARE = "knowledge_share"
    PROGRESS_UPDATE = "progress_update"
    DEPENDENCY_ALERT = "dependency_alert"

class MessagePriority(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class SmartMessage:
    """지능적 메시지 구조"""
    message_id: str
    from_role: str
    to_role: str
    message_type: MessageType
    priority: MessagePriority
    subject: str
    content: Dict[str, Any]
    context: Dict[str, Any]
    expected_response_time: timedelta
    requires_response: bool
    timestamp: datetime
    read_by: List[str] = None
    responded_to: bool = False

class ActiveCommunicationEngine:
    """능동적 커뮤니케이션 엔진"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.communication_dir = self.project_root / "communication"
        self.active_conversations = {}
        self.pending_questions = {}
        self.collaboration_requests = {}
        
    def generate_proactive_questions(self, role_id: str, context: Dict) -> List[SmartMessage]:
        """역할별 상황에 맞는 능동적 질문 생성"""
        questions = []
        
        # 의존성 관련 질문
        if context.get('waiting_for_dependencies'):
            for dep_role in context['waiting_for_dependencies']:
                question = SmartMessage(
                    message_id=f"dep_check_{role_id}_{dep_role}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    from_role=role_id,
                    to_role=dep_role,
                    message_type=MessageType.QUESTION,
                    priority=MessagePriority.HIGH,
                    subject=f"{role_id}의 작업 진행을 위한 의존성 확인",
                    content={
                        "question": f"안녕하세요, {dep_role}님. {role_id} 역할에서 작업을 진행하기 위해 귀하의 산출물이 필요합니다.",
                        "specific_needs": self._identify_specific_needs(role_id, dep_role),
                        "current_blockers": context.get('current_blockers', []),
                        "expected_timeline": self._calculate_expected_timeline(role_id)
                    },
                    context={
                        "dependency_chain": context.get('dependency_chain', []),
                        "project_urgency": context.get('project_urgency', 'medium')
                    },
                    expected_response_time=timedelta(hours=2),
                    requires_response=True,
                    timestamp=datetime.now()
                )
                questions.append(question)
        
        # 품질 관련 질문
        if self._should_ask_quality_questions(role_id, context):
            questions.extend(self._generate_quality_questions(role_id, context))
        
        # 협업 제안
        if self._should_propose_collaboration(role_id, context):
            questions.extend(self._generate_collaboration_proposals(role_id, context))
        
        return questions
    
    def generate_feedback_requests(self, role_id: str, deliverable: str, context: Dict) -> List[SmartMessage]:
        """산출물에 대한 피드백 요청 생성"""
        feedback_requests = []
        
        # 해당 산출물을 사용할 역할들 식별
        potential_reviewers = self._identify_reviewers(role_id, deliverable)
        
        for reviewer_role in potential_reviewers:
            request = SmartMessage(
                message_id=f"feedback_{role_id}_{reviewer_role}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                from_role=role_id,
                to_role=reviewer_role,
                message_type=MessageType.FEEDBACK_REQUEST,
                priority=MessagePriority.MEDIUM,
                subject=f"{deliverable} 산출물에 대한 전문적 피드백 요청",
                content={
                    "deliverable_name": deliverable,
                    "deliverable_path": f"roles/{role_id}/deliverables/{deliverable}",
                    "specific_feedback_areas": self._identify_feedback_areas(role_id, reviewer_role, deliverable),
                    "questions_for_reviewer": self._generate_specific_questions(role_id, reviewer_role, deliverable),
                    "context_background": context.get('background', {}),
                    "deadline_for_feedback": (datetime.now() + timedelta(hours=4)).isoformat()
                },
                context={
                    "deliverable_importance": self._assess_deliverable_importance(deliverable),
                    "project_phase": context.get('project_phase', 'unknown'),
                    "related_deliverables": context.get('related_deliverables', [])
                },
                expected_response_time=timedelta(hours=4),
                requires_response=True,
                timestamp=datetime.now()
            )
            feedback_requests.append(request)
        
        return feedback_requests
    
    def generate_clarification_requests(self, role_id: str, unclear_requirements: List[str]) -> List[SmartMessage]:
        """불명확한 요구사항에 대한 명확화 요청"""
        requests = []
        
        for requirement in unclear_requirements:
            # 해당 요구사항의 소유자 식별
            owner_role = self._identify_requirement_owner(requirement)
            
            if owner_role:
                request = SmartMessage(
                    message_id=f"clarify_{role_id}_{owner_role}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    from_role=role_id,
                    to_role=owner_role,
                    message_type=MessageType.CLARIFICATION_REQUEST,
                    priority=MessagePriority.HIGH,
                    subject=f"요구사항 명확화 요청: {requirement}",
                    content={
                        "unclear_requirement": requirement,
                        "specific_confusion_points": self._identify_confusion_points(requirement),
                        "proposed_interpretations": self._generate_interpretation_options(requirement),
                        "impact_on_work": self._assess_clarification_impact(role_id, requirement),
                        "suggested_resolution_approach": self._suggest_resolution_approach(requirement)
                    },
                    context={
                        "current_task": f"{role_id} 역할의 현재 작업",
                        "dependency_impact": self._assess_dependency_impact(role_id, requirement)
                    },
                    expected_response_time=timedelta(hours=1),
                    requires_response=True,
                    timestamp=datetime.now()
                )
                requests.append(request)
        
        return requests
    
    def initiate_peer_review(self, role_id: str, deliverable: str, review_criteria: Dict) -> List[SmartMessage]:
        """동료 검토 프로세스 시작"""
        review_requests = []
        
        # 적절한 리뷰어 식별
        reviewers = self._identify_peer_reviewers(role_id, deliverable)
        
        for reviewer in reviewers:
            request = SmartMessage(
                message_id=f"peer_review_{role_id}_{reviewer}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                from_role=role_id,
                to_role=reviewer,
                message_type=MessageType.REVIEW_REQUEST,
                priority=MessagePriority.HIGH,
                subject=f"동료 검토 요청: {deliverable}",
                content={
                    "deliverable_name": deliverable,
                    "deliverable_path": f"roles/{role_id}/deliverables/{deliverable}",
                    "review_criteria": review_criteria,
                    "specific_review_points": self._generate_review_points(role_id, reviewer, deliverable),
                    "review_deadline": (datetime.now() + timedelta(hours=6)).isoformat(),
                    "review_template": self._generate_review_template(deliverable),
                    "context_information": self._gather_review_context(role_id, deliverable)
                },
                context={
                    "review_importance": "critical",
                    "quality_gates": review_criteria.get('quality_gates', []),
                    "previous_feedback": self._get_previous_feedback(deliverable)
                },
                expected_response_time=timedelta(hours=6),
                requires_response=True,
                timestamp=datetime.now()
            )
            review_requests.append(request)
        
        return review_requests
    
    def propose_knowledge_sharing(self, role_id: str, learned_insights: Dict) -> List[SmartMessage]:
        """지식 공유 제안"""
        sharing_messages = []
        
        # 관련 역할들 식별
        interested_roles = self._identify_knowledge_beneficiaries(role_id, learned_insights)
        
        for target_role in interested_roles:
            message = SmartMessage(
                message_id=f"knowledge_share_{role_id}_{target_role}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                from_role=role_id,
                to_role=target_role,
                message_type=MessageType.KNOWLEDGE_SHARE,
                priority=MessagePriority.MEDIUM,
                subject=f"{role_id}에서 발견한 유용한 인사이트 공유",
                content={
                    "insights": learned_insights,
                    "relevance_to_target": self._explain_relevance(role_id, target_role, learned_insights),
                    "suggested_applications": self._suggest_applications(target_role, learned_insights),
                    "supporting_evidence": learned_insights.get('evidence', []),
                    "follow_up_discussion": self._suggest_follow_up(role_id, target_role, learned_insights)
                },
                context={
                    "knowledge_type": learned_insights.get('type', 'general'),
                    "confidence_level": learned_insights.get('confidence', 'medium'),
                    "source_context": learned_insights.get('source', {})
                },
                expected_response_time=timedelta(hours=8),
                requires_response=False,
                timestamp=datetime.now()
            )
            sharing_messages.append(message)
        
        return sharing_messages
    
    def escalate_concerns(self, role_id: str, concerns: List[Dict]) -> List[SmartMessage]:
        """우려사항 에스컬레이션"""
        escalation_messages = []
        
        for concern in concerns:
            # 에스컬레이션 대상 결정
            escalation_target = self._determine_escalation_target(role_id, concern)
            
            message = SmartMessage(
                message_id=f"escalation_{role_id}_{escalation_target}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                from_role=role_id,
                to_role=escalation_target,
                message_type=MessageType.CONCERN_REPORT,
                priority=MessagePriority.CRITICAL,
                subject=f"중요 우려사항 에스컬레이션: {concern.get('title', 'Unknown')}",
                content={
                    "concern_description": concern.get('description', ''),
                    "potential_impact": concern.get('impact', {}),
                    "suggested_solutions": concern.get('solutions', []),
                    "urgency_level": concern.get('urgency', 'high'),
                    "affected_roles": concern.get('affected_roles', []),
                    "decision_needed": concern.get('decision_needed', ''),
                    "escalation_reason": self._explain_escalation_reason(role_id, concern)
                },
                context={
                    "project_risk": self._assess_project_risk(concern),
                    "timeline_impact": self._assess_timeline_impact(concern),
                    "resource_implications": concern.get('resource_impact', {})
                },
                expected_response_time=timedelta(hours=2),
                requires_response=True,
                timestamp=datetime.now()
            )
            escalation_messages.append(message)
        
        return escalation_messages
    
    # Helper methods
    def _identify_specific_needs(self, role_id: str, dep_role: str) -> List[str]:
        """특정 의존성 요구사항 식별"""
        needs_mapping = {
            "requirements_analyst": {
                "business_analyst": ["기능 명세서", "비즈니스 규칙", "사용자 스토리"],
                "product_owner": ["제품 비전", "우선순위", "수용 기준"]
            },
            "system_architect": {
                "requirements_analyst": ["기술 요구사항", "비기능 요구사항", "제약사항"],
                "business_analyst": ["비즈니스 프로세스", "데이터 플로우"]
            }
        }
        return needs_mapping.get(role_id, {}).get(dep_role, ["일반적인 산출물"])
    
    def _calculate_expected_timeline(self, role_id: str) -> str:
        """예상 타임라인 계산"""
        # 역할별 일반적인 작업 시간 추정
        timeline_estimates = {
            "requirements_analyst": "6-8시간",
            "system_architect": "8-12시간",
            "frontend_developer": "12-16시간",
            "backend_developer": "12-16시간"
        }
        return timeline_estimates.get(role_id, "4-6시간")
    
    def _should_ask_quality_questions(self, role_id: str, context: Dict) -> bool:
        """품질 관련 질문이 필요한지 판단"""
        return (
            context.get('deliverable_count', 0) > 0 and
            context.get('last_quality_check') is None
        )
    
    def _generate_quality_questions(self, role_id: str, context: Dict) -> List[SmartMessage]:
        """품질 관련 질문 생성"""
        # 품질 관련 질문 로직 구현
        return []
    
    def _should_propose_collaboration(self, role_id: str, context: Dict) -> bool:
        """협업 제안이 필요한지 판단"""
        return (
            context.get('complexity_level', 'medium') in ['high', 'critical'] and
            context.get('collaboration_opportunities', [])
        )
    
    def _generate_collaboration_proposals(self, role_id: str, context: Dict) -> List[SmartMessage]:
        """협업 제안 생성"""
        # 협업 제안 로직 구현
        return []
    
    def _identify_reviewers(self, role_id: str, deliverable: str) -> List[str]:
        """적절한 리뷰어 식별"""
        reviewer_mapping = {
            "business_requirements.md": ["product_owner", "requirements_analyst", "stakeholder"],
            "system_architecture.md": ["solution_architect", "senior_developer", "technical_reviewer"],
            "database_schema.sql": ["backend_developer", "database_designer", "technical_reviewer"]
        }
        return reviewer_mapping.get(deliverable, ["technical_reviewer"])
    
    def _identify_feedback_areas(self, role_id: str, reviewer_role: str, deliverable: str) -> List[str]:
        """피드백 영역 식별"""
        feedback_areas = {
            "product_owner": ["비즈니스 가치", "요구사항 완전성", "우선순위 적절성"],
            "technical_reviewer": ["기술적 정확성", "구현 가능성", "코드 품질"],
            "senior_developer": ["아키텍처 적절성", "확장성", "성능 고려사항"]
        }
        return feedback_areas.get(reviewer_role, ["일반적인 품질"])
    
    def _generate_specific_questions(self, role_id: str, reviewer_role: str, deliverable: str) -> List[str]:
        """구체적인 질문 생성"""
        questions = [
            f"{deliverable}의 내용이 {reviewer_role} 관점에서 충분히 상세한가요?",
            f"누락된 중요 사항이 있다면 무엇인가요?",
            f"다음 단계 작업을 위해 추가로 필요한 정보가 있나요?",
            f"현재 내용에서 개선이 필요한 부분은 어디인가요?"
        ]
        return questions
    
    def _assess_deliverable_importance(self, deliverable: str) -> str:
        """산출물 중요도 평가"""
        critical_deliverables = [
            "business_requirements.md",
            "system_architecture.md",
            "api_specifications.md"
        ]
        return "critical" if deliverable in critical_deliverables else "normal"
    
    def _identify_requirement_owner(self, requirement: str) -> Optional[str]:
        """요구사항 소유자 식별"""
        # 간단한 키워드 기반 매핑
        if "business" in requirement.lower():
            return "business_analyst"
        elif "technical" in requirement.lower():
            return "requirements_analyst"
        elif "ui" in requirement.lower() or "ux" in requirement.lower():
            return "ui_ux_designer"
        else:
            return "product_owner"
    
    def _identify_confusion_points(self, requirement: str) -> List[str]:
        """혼란 지점 식별"""
        return [
            "구체적인 구현 방법이 불분명함",
            "성공 기준이 명확하지 않음",
            "다른 요구사항과의 우선순위 불분명",
            "기술적 제약사항 고려 필요"
        ]
    
    def _generate_interpretation_options(self, requirement: str) -> List[str]:
        """해석 옵션 생성"""
        return [
            "해석 옵션 A: 최소 기능 구현",
            "해석 옵션 B: 완전한 기능 구현",
            "해석 옵션 C: 단계적 구현"
        ]
    
    def _assess_clarification_impact(self, role_id: str, requirement: str) -> str:
        """명확화 필요성의 영향도 평가"""
        return f"{role_id}의 작업 진행에 직접적인 영향을 미침"
    
    def _suggest_resolution_approach(self, requirement: str) -> str:
        """해결 접근법 제안"""
        return "관련 이해관계자들과의 짧은 회의를 통한 신속한 결정 제안"
    
    def _assess_dependency_impact(self, role_id: str, requirement: str) -> str:
        """의존성 영향도 평가"""
        return f"하위 역할들의 작업 일정에 영향 가능성 있음"
    
    def _identify_peer_reviewers(self, role_id: str, deliverable: str) -> List[str]:
        """동료 리뷰어 식별"""
        peer_mapping = {
            "business_analyst": ["requirements_analyst", "product_owner"],
            "system_architect": ["solution_architect", "senior_developer"],
            "frontend_developer": ["fullstack_developer", "ui_ux_designer"],
            "backend_developer": ["fullstack_developer", "database_designer"]
        }
        return peer_mapping.get(role_id, ["technical_reviewer"])
    
    def _generate_review_points(self, role_id: str, reviewer: str, deliverable: str) -> List[str]:
        """리뷰 포인트 생성"""
        return [
            "내용의 완전성 및 정확성",
            "명세의 명확성 및 이해도",
            "다음 단계 작업에 필요한 정보 충족도",
            "프로젝트 목표와의 일치성"
        ]
    
    def _generate_review_template(self, deliverable: str) -> Dict[str, Any]:
        """리뷰 템플릿 생성"""
        return {
            "overall_quality": {"scale": "1-5", "description": "전반적인 품질 평가"},
            "completeness": {"scale": "1-5", "description": "내용 완성도"},
            "clarity": {"scale": "1-5", "description": "명확성"},
            "specific_feedback": {"type": "text", "description": "구체적인 피드백"},
            "approval_status": {"options": ["승인", "조건부 승인", "재작업 필요"], "description": "승인 상태"}
        }
    
    def _gather_review_context(self, role_id: str, deliverable: str) -> Dict[str, Any]:
        """리뷰 컨텍스트 수집"""
        return {
            "project_phase": "requirements_analysis",
            "dependencies": [],
            "related_deliverables": [],
            "urgency": "high"
        }
    
    def _get_previous_feedback(self, deliverable: str) -> List[Dict]:
        """이전 피드백 조회"""
        return []
    
    def _identify_knowledge_beneficiaries(self, role_id: str, insights: Dict) -> List[str]:
        """지식 수혜자 식별"""
        insight_type = insights.get('type', 'general')
        
        beneficiary_mapping = {
            "technical": ["system_architect", "senior_developer", "technical_reviewer"],
            "business": ["business_analyst", "product_owner", "requirements_analyst"],
            "design": ["ui_ux_designer", "ux_researcher", "frontend_developer"],
            "process": ["project_manager", "devops_engineer", "qa_tester"]
        }
        
        return beneficiary_mapping.get(insight_type, ["project_manager"])
    
    def _explain_relevance(self, role_id: str, target_role: str, insights: Dict) -> str:
        """관련성 설명"""
        return f"{role_id}에서 발견한 인사이트가 {target_role}의 작업에 도움이 될 것으로 판단됩니다."
    
    def _suggest_applications(self, target_role: str, insights: Dict) -> List[str]:
        """적용 방안 제안"""
        return [
            f"{target_role}의 현재 작업에 직접 적용 가능",
            "향후 유사한 상황에서 참고 자료로 활용",
            "팀 전체의 지식 베이스 향상에 기여"
        ]
    
    def _suggest_follow_up(self, role_id: str, target_role: str, insights: Dict) -> List[str]:
        """후속 논의 제안"""
        return [
            "필요시 추가 상세 설명 제공",
            "실제 적용 과정에서의 협업 가능",
            "관련 경험 공유 및 토론"
        ]
    
    def _determine_escalation_target(self, role_id: str, concern: Dict) -> str:
        """에스컬레이션 대상 결정"""
        concern_type = concern.get('type', 'general')
        
        escalation_mapping = {
            "technical": "senior_developer",
            "business": "product_owner",
            "process": "project_manager",
            "resource": "project_owner",
            "timeline": "project_manager"
        }
        
        return escalation_mapping.get(concern_type, "project_manager")
    
    def _explain_escalation_reason(self, role_id: str, concern: Dict) -> str:
        """에스컬레이션 이유 설명"""
        return f"{role_id} 수준에서 해결하기 어려운 중요한 문제로 판단되어 에스컬레이션합니다."
    
    def _assess_project_risk(self, concern: Dict) -> str:
        """프로젝트 리스크 평가"""
        impact = concern.get('impact', {})
        severity = impact.get('severity', 'medium')
        return f"프로젝트 리스크 수준: {severity}"
    
    def _assess_timeline_impact(self, concern: Dict) -> str:
        """타임라인 영향도 평가"""
        return concern.get('timeline_impact', '일정에 미치는 영향 분석 필요')

    def send_message(self, message: SmartMessage) -> bool:
        """메시지 전송"""
        try:
            # 메시지를 YAML 파일로 저장
            comm_dir = self.communication_dir / f"from_{message.from_role}"
            comm_dir.mkdir(parents=True, exist_ok=True)
            
            message_file = comm_dir / f"{message.timestamp.strftime('%Y%m%d_%H%M%S')}_{message.message_type.value}_{message.to_role}.yaml"
            
            message_data = {
                'message_id': message.message_id,
                'from_role': message.from_role,
                'to_role': message.to_role,
                'type': message.message_type.value,
                'priority': message.priority.value,
                'subject': message.subject,
                'content': message.content,
                'context': message.context,
                'expected_response_time': message.expected_response_time.total_seconds(),
                'requires_response': message.requires_response,
                'timestamp': message.timestamp.isoformat()
            }
            
            with open(message_file, 'w', encoding='utf-8') as f:
                yaml.dump(message_data, f, default_flow_style=False, allow_unicode=True)
            
            return True
            
        except Exception as e:
            print(f"메시지 전송 실패: {str(e)}")
            return False
    
    def process_incoming_messages(self, role_id: str) -> List[SmartMessage]:
        """수신 메시지 처리"""
        incoming_dir = self.communication_dir / f"to_{role_id}"
        messages = []
        
        if incoming_dir.exists():
            for message_file in incoming_dir.glob("*.yaml"):
                try:
                    with open(message_file, 'r', encoding='utf-8') as f:
                        data = yaml.safe_load(f)
                    
                    message = SmartMessage(
                        message_id=data['message_id'],
                        from_role=data['from_role'],
                        to_role=data['to_role'],
                        message_type=MessageType(data['type']),
                        priority=MessagePriority(data['priority']),
                        subject=data['subject'],
                        content=data['content'],
                        context=data['context'],
                        expected_response_time=timedelta(seconds=data['expected_response_time']),
                        requires_response=data['requires_response'],
                        timestamp=datetime.fromisoformat(data['timestamp'])
                    )
                    messages.append(message)
                    
                except Exception as e:
                    print(f"메시지 로드 실패 ({message_file}): {str(e)}")
        
        return messages

def main():
    """테스트 및 데모"""
    comm_engine = ActiveCommunicationEngine("/home/jungh/workspace/web_community_project")
    
    # 예시: 능동적 질문 생성
    context = {
        'waiting_for_dependencies': ['business_analyst'],
        'current_blockers': ['요구사항 불명확'],
        'project_urgency': 'high'
    }
    
    questions = comm_engine.generate_proactive_questions('requirements_analyst', context)
    
    for question in questions:
        print(f"생성된 질문: {question.subject}")
        comm_engine.send_message(question)

if __name__ == "__main__":
    main()