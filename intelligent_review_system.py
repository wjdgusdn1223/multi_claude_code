#!/usr/bin/env python3
"""
Intelligent Review and Approval System for Multi-Agent Claude Code
지능적 리뷰 및 승인 시스템 - AI 간 매우 이성적이고 엄격한 리뷰 프로세스
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import hashlib
import re

class ReviewType(Enum):
    TECHNICAL_REVIEW = "technical_review"
    BUSINESS_REVIEW = "business_review"
    QUALITY_REVIEW = "quality_review"
    SECURITY_REVIEW = "security_review"
    ARCHITECTURE_REVIEW = "architecture_review"
    CODE_REVIEW = "code_review"
    DESIGN_REVIEW = "design_review"
    FINAL_APPROVAL = "final_approval"

class ReviewStatus(Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    CONDITIONAL_APPROVAL = "conditional_approval"

class CriticalityLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class ReviewCriterion:
    """리뷰 기준"""
    criterion_id: str
    name: str
    description: str
    weight: float  # 가중치 (0.0 - 1.0)
    mandatory: bool
    validation_rules: List[str]
    evaluation_method: str

@dataclass
class ReviewIssue:
    """리뷰 이슈"""
    issue_id: str
    criterion_id: str
    severity: CriticalityLevel
    title: str
    description: str
    location: str  # 파일 경로나 섹션
    suggested_fix: str
    blocking: bool  # 승인을 막는 이슈인지
    evidence: List[str]

@dataclass
class ReviewResult:
    """리뷰 결과"""
    review_id: str
    reviewer_role: str
    reviewee_role: str
    deliverable_path: str
    review_type: ReviewType
    status: ReviewStatus
    overall_score: float  # 0.0 - 1.0
    created_at: datetime
    completed_at: Optional[datetime]
    issues: List[ReviewIssue]
    recommendations: List[str]
    decision_rationale: str
    revision_required: bool
    next_reviewer: Optional[str]

class IntelligentReviewEngine:
    """지능적 리뷰 엔진"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.reviews_dir = self.project_root / "reviews"
        self.criteria_dir = self.project_root / "review_criteria"
        
        # 디렉토리 생성
        self.reviews_dir.mkdir(exist_ok=True)
        self.criteria_dir.mkdir(exist_ok=True)
        
        # 리뷰 기준 초기화
        self.review_criteria = self._initialize_review_criteria()
        self.active_reviews: Dict[str, ReviewResult] = {}
        
        # 역할별 리뷰 권한 매핑
        self.reviewer_capabilities = self._initialize_reviewer_capabilities()
        
        print("🔍 Intelligent Review System 초기화 완료")
    
    def _initialize_review_criteria(self) -> Dict[str, List[ReviewCriterion]]:
        """리뷰 기준 초기화"""
        criteria = {}
        
        # 기술 리뷰 기준
        criteria[ReviewType.TECHNICAL_REVIEW.value] = [
            ReviewCriterion(
                criterion_id="tech_accuracy",
                name="기술적 정확성",
                description="기술적 내용의 정확성과 실현 가능성",
                weight=0.3,
                mandatory=True,
                validation_rules=[
                    "기술 스택 호환성 확인",
                    "API 명세 정확성 검증",
                    "데이터 모델 일관성 확인",
                    "성능 요구사항 달성 가능성"
                ],
                evaluation_method="technical_analysis"
            ),
            ReviewCriterion(
                criterion_id="implementation_feasibility",
                name="구현 가능성",
                description="제안된 솔루션의 실제 구현 가능성",
                weight=0.25,
                mandatory=True,
                validation_rules=[
                    "기술적 복잡도 적절성",
                    "개발 시간 현실성",
                    "리소스 요구사항 합리성",
                    "의존성 관리 적절성"
                ],
                evaluation_method="feasibility_analysis"
            ),
            ReviewCriterion(
                criterion_id="scalability",
                name="확장성",
                description="시스템의 확장 가능성과 유연성",
                weight=0.2,
                mandatory=False,
                validation_rules=[
                    "부하 증가 대응 능력",
                    "기능 확장 용이성",
                    "아키텍처 유연성"
                ],
                evaluation_method="scalability_assessment"
            ),
            ReviewCriterion(
                criterion_id="security_compliance",
                name="보안 준수",
                description="보안 요구사항 준수 여부",
                weight=0.25,
                mandatory=True,
                validation_rules=[
                    "인증/인가 체계 적절성",
                    "데이터 암호화 방안",
                    "보안 취약점 검토",
                    "개인정보 보호 준수"
                ],
                evaluation_method="security_review"
            )
        ]
        
        # 비즈니스 리뷰 기준
        criteria[ReviewType.BUSINESS_REVIEW.value] = [
            ReviewCriterion(
                criterion_id="business_value",
                name="비즈니스 가치",
                description="비즈니스 목표와의 일치성",
                weight=0.4,
                mandatory=True,
                validation_rules=[
                    "비즈니스 목표 달성 기여도",
                    "ROI 정당성",
                    "사용자 가치 창출",
                    "경쟁 우위 확보"
                ],
                evaluation_method="business_analysis"
            ),
            ReviewCriterion(
                criterion_id="requirement_completeness",
                name="요구사항 완전성",
                description="비즈니스 요구사항의 완전성과 명확성",
                weight=0.3,
                mandatory=True,
                validation_rules=[
                    "모든 이해관계자 요구사항 반영",
                    "기능적 요구사항 완전성",
                    "비기능적 요구사항 명확성",
                    "제약사항 식별 완료"
                ],
                evaluation_method="completeness_check"
            ),
            ReviewCriterion(
                criterion_id="user_experience",
                name="사용자 경험",
                description="최종 사용자 관점에서의 경험 품질",
                weight=0.2,
                mandatory=False,
                validation_rules=[
                    "사용성 고려",
                    "접근성 준수",
                    "사용자 여정 최적화"
                ],
                evaluation_method="ux_evaluation"
            ),
            ReviewCriterion(
                criterion_id="risk_assessment",
                name="리스크 평가",
                description="비즈니스 리스크 식별 및 대응방안",
                weight=0.1,
                mandatory=False,
                validation_rules=[
                    "주요 리스크 식별",
                    "리스크 대응방안 수립",
                    "리스크 영향도 평가"
                ],
                evaluation_method="risk_analysis"
            )
        ]
        
        # 품질 리뷰 기준
        criteria[ReviewType.QUALITY_REVIEW.value] = [
            ReviewCriterion(
                criterion_id="documentation_quality",
                name="문서화 품질",
                description="문서의 명확성, 완전성, 일관성",
                weight=0.25,
                mandatory=True,
                validation_rules=[
                    "내용 명확성",
                    "구조 일관성",
                    "정보 완전성",
                    "가독성"
                ],
                evaluation_method="documentation_analysis"
            ),
            ReviewCriterion(
                criterion_id="consistency",
                name="일관성",
                description="프로젝트 전체와의 일관성",
                weight=0.25,
                mandatory=True,
                validation_rules=[
                    "명명 규칙 일관성",
                    "스타일 가이드 준수",
                    "다른 문서와의 일치성",
                    "용어 사용 일관성"
                ],
                evaluation_method="consistency_check"
            ),
            ReviewCriterion(
                criterion_id="testability",
                name="테스트 가능성",
                description="테스트 가능한 형태로 명세되었는지",
                weight=0.25,
                mandatory=True,
                validation_rules=[
                    "테스트 케이스 도출 가능성",
                    "검증 기준 명확성",
                    "측정 가능한 성공 기준"
                ],
                evaluation_method="testability_assessment"
            ),
            ReviewCriterion(
                criterion_id="maintainability",
                name="유지보수성",
                description="향후 유지보수의 용이성",
                weight=0.25,
                mandatory=False,
                validation_rules=[
                    "코드 가독성",
                    "모듈화 수준",
                    "문서화 수준",
                    "변경 영향도 최소화"
                ],
                evaluation_method="maintainability_check"
            )
        ]
        
        return criteria
    
    def _initialize_reviewer_capabilities(self) -> Dict[str, List[ReviewType]]:
        """역할별 리뷰 능력 매핑"""
        return {
            "technical_reviewer": [
                ReviewType.TECHNICAL_REVIEW,
                ReviewType.QUALITY_REVIEW,
                ReviewType.CODE_REVIEW
            ],
            "senior_developer": [
                ReviewType.TECHNICAL_REVIEW,
                ReviewType.ARCHITECTURE_REVIEW,
                ReviewType.CODE_REVIEW
            ],
            "system_architect": [
                ReviewType.ARCHITECTURE_REVIEW,
                ReviewType.TECHNICAL_REVIEW
            ],
            "product_owner": [
                ReviewType.BUSINESS_REVIEW,
                ReviewType.FINAL_APPROVAL
            ],
            "business_analyst": [
                ReviewType.BUSINESS_REVIEW,
                ReviewType.QUALITY_REVIEW
            ],
            "security_tester": [
                ReviewType.SECURITY_REVIEW
            ],
            "qa_tester": [
                ReviewType.QUALITY_REVIEW
            ],
            "project_manager": [
                ReviewType.FINAL_APPROVAL
            ]
        }
    
    def request_review(self, 
                      deliverable_path: str,
                      reviewee_role: str,
                      review_type: ReviewType,
                      priority: CriticalityLevel = CriticalityLevel.MEDIUM,
                      custom_criteria: List[str] = None) -> str:
        """리뷰 요청"""
        
        # 적절한 리뷰어 식별
        reviewer_role = self._identify_best_reviewer(review_type, reviewee_role)
        
        if not reviewer_role:
            raise ValueError(f"적절한 리뷰어를 찾을 수 없습니다: {review_type}")
        
        # 리뷰 ID 생성
        review_id = f"{review_type.value}_{reviewee_role}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # 리뷰 결과 객체 생성
        review_result = ReviewResult(
            review_id=review_id,
            reviewer_role=reviewer_role,
            reviewee_role=reviewee_role,
            deliverable_path=deliverable_path,
            review_type=review_type,
            status=ReviewStatus.PENDING,
            overall_score=0.0,
            created_at=datetime.now(),
            completed_at=None,
            issues=[],
            recommendations=[],
            decision_rationale="",
            revision_required=False,
            next_reviewer=None
        )
        
        # 리뷰 저장
        self.active_reviews[review_id] = review_result
        self._save_review_result(review_result)
        
        # 리뷰어에게 리뷰 요청 메시지 전송
        self._send_review_request(review_result, custom_criteria)
        
        print(f"📋 리뷰 요청: {deliverable_path} ({review_type.value}) -> {reviewer_role}")
        return review_id
    
    def conduct_intelligent_review(self, review_id: str) -> ReviewResult:
        """지능적 리뷰 수행"""
        
        review_result = self.active_reviews.get(review_id)
        if not review_result:
            raise ValueError(f"리뷰를 찾을 수 없습니다: {review_id}")
        
        print(f"🔍 지능적 리뷰 시작: {review_id}")
        
        # 리뷰 상태 업데이트
        review_result.status = ReviewStatus.IN_REVIEW
        
        # 산출물 분석
        deliverable_content = self._load_deliverable(review_result.deliverable_path)
        
        # 리뷰 기준 적용
        criteria_list = self.review_criteria.get(review_result.review_type.value, [])
        
        total_score = 0.0
        total_weight = 0.0
        all_issues = []
        recommendations = []
        
        for criterion in criteria_list:
            # 각 기준별 평가
            score, issues, recs = self._evaluate_criterion(
                criterion, 
                deliverable_content, 
                review_result
            )
            
            total_score += score * criterion.weight
            total_weight += criterion.weight
            all_issues.extend(issues)
            recommendations.extend(recs)
            
            print(f"  📊 {criterion.name}: {score:.2f}")
        
        # 전체 점수 계산
        overall_score = total_score / total_weight if total_weight > 0 else 0.0
        
        # 리뷰 결과 업데이트
        review_result.overall_score = overall_score
        review_result.issues = all_issues
        review_result.recommendations = recommendations
        review_result.completed_at = datetime.now()
        
        # 승인/거부 결정
        decision = self._make_approval_decision(review_result)
        review_result.status = decision['status']
        review_result.decision_rationale = decision['rationale']
        review_result.revision_required = decision['revision_required']
        review_result.next_reviewer = decision.get('next_reviewer')
        
        # 결과 저장
        self._save_review_result(review_result)
        
        # 리뷰 결과 통지
        self._notify_review_completion(review_result)
        
        print(f"✅ 리뷰 완료: {review_id} - {review_result.status.value} (점수: {overall_score:.2f})")
        
        return review_result
    
    def _identify_best_reviewer(self, review_type: ReviewType, reviewee_role: str) -> Optional[str]:
        """최적 리뷰어 식별"""
        
        # 리뷰 타입별 적절한 리뷰어 찾기
        candidate_reviewers = []
        
        for role, capabilities in self.reviewer_capabilities.items():
            if review_type in capabilities and role != reviewee_role:
                candidate_reviewers.append(role)
        
        if not candidate_reviewers:
            return None
        
        # 우선순위 기반 선택
        priority_map = {
            ReviewType.TECHNICAL_REVIEW: ["senior_developer", "technical_reviewer", "system_architect"],
            ReviewType.BUSINESS_REVIEW: ["product_owner", "business_analyst"],
            ReviewType.ARCHITECTURE_REVIEW: ["system_architect", "senior_developer"],
            ReviewType.SECURITY_REVIEW: ["security_tester"],
            ReviewType.QUALITY_REVIEW: ["qa_tester", "technical_reviewer"],
            ReviewType.FINAL_APPROVAL: ["project_manager", "product_owner"]
        }
        
        preferred_order = priority_map.get(review_type, candidate_reviewers)
        
        for preferred_reviewer in preferred_order:
            if preferred_reviewer in candidate_reviewers:
                return preferred_reviewer
        
        return candidate_reviewers[0] if candidate_reviewers else None
    
    def _load_deliverable(self, deliverable_path: str) -> Dict[str, Any]:
        """산출물 로드 및 분석"""
        
        full_path = self.project_root / deliverable_path
        
        if not full_path.exists():
            return {"error": "파일을 찾을 수 없음", "path": deliverable_path}
        
        try:
            # 파일 확장자에 따른 처리
            if full_path.suffix.lower() in ['.md', '.txt']:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                return {
                    "file_type": "text",
                    "content": content,
                    "line_count": len(content.splitlines()),
                    "word_count": len(content.split()),
                    "char_count": len(content),
                    "sections": self._extract_markdown_sections(content)
                }
            
            elif full_path.suffix.lower() in ['.json']:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                return {
                    "file_type": "json",
                    "content": data,
                    "structure": self._analyze_json_structure(data)
                }
            
            elif full_path.suffix.lower() in ['.yaml', '.yml']:
                with open(full_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                
                return {
                    "file_type": "yaml",
                    "content": data,
                    "structure": self._analyze_yaml_structure(data)
                }
            
            else:
                return {"error": "지원하지 않는 파일 형식", "file_type": full_path.suffix}
        
        except Exception as e:
            return {"error": f"파일 로드 실패: {str(e)}"}
    
    def _evaluate_criterion(self, 
                          criterion: ReviewCriterion, 
                          deliverable_content: Dict[str, Any], 
                          review_result: ReviewResult) -> Tuple[float, List[ReviewIssue], List[str]]:
        """기준별 평가"""
        
        if criterion.evaluation_method == "technical_analysis":
            return self._evaluate_technical_accuracy(criterion, deliverable_content, review_result)
        elif criterion.evaluation_method == "feasibility_analysis":
            return self._evaluate_implementation_feasibility(criterion, deliverable_content, review_result)
        elif criterion.evaluation_method == "business_analysis":
            return self._evaluate_business_value(criterion, deliverable_content, review_result)
        elif criterion.evaluation_method == "documentation_analysis":
            return self._evaluate_documentation_quality(criterion, deliverable_content, review_result)
        elif criterion.evaluation_method == "consistency_check":
            return self._evaluate_consistency(criterion, deliverable_content, review_result)
        else:
            return self._evaluate_generic_criterion(criterion, deliverable_content, review_result)
    
    def _evaluate_technical_accuracy(self, 
                                   criterion: ReviewCriterion, 
                                   content: Dict[str, Any], 
                                   review_result: ReviewResult) -> Tuple[float, List[ReviewIssue], List[str]]:
        """기술적 정확성 평가"""
        
        issues = []
        recommendations = []
        score = 1.0  # 기본 만점에서 시작
        
        if content.get("error"):
            issues.append(ReviewIssue(
                issue_id=f"tech_acc_001_{datetime.now().strftime('%H%M%S')}",
                criterion_id=criterion.criterion_id,
                severity=CriticalityLevel.CRITICAL,
                title="파일 로드 오류",
                description=content["error"],
                location=review_result.deliverable_path,
                suggested_fix="파일 형식과 인코딩을 확인하세요",
                blocking=True,
                evidence=[]
            ))
            return 0.0, issues, recommendations
        
        # 마크다운 문서인 경우
        if content.get("file_type") == "text":
            text_content = content.get("content", "")
            
            # 기술 용어 일관성 확인
            tech_terms = ["API", "REST", "HTTP", "JSON", "JWT", "PostgreSQL", "React", "Node.js"]
            inconsistent_terms = self._check_technical_term_consistency(text_content, tech_terms)
            
            for term_issue in inconsistent_terms:
                issues.append(ReviewIssue(
                    issue_id=f"tech_acc_002_{len(issues)}",
                    criterion_id=criterion.criterion_id,
                    severity=CriticalityLevel.MEDIUM,
                    title=f"기술 용어 불일치: {term_issue['term']}",
                    description=f"기술 용어 '{term_issue['term']}'이 일관되지 않게 사용됨",
                    location=f"라인 {term_issue['lines']}",
                    suggested_fix=f"'{term_issue['standard_form']}'으로 통일 사용",
                    blocking=False,
                    evidence=term_issue['examples']
                ))
                score -= 0.1
            
            # API 명세 검증
            if "api" in text_content.lower() or "endpoint" in text_content.lower():
                api_issues = self._validate_api_specifications(text_content)
                issues.extend(api_issues)
                score -= len(api_issues) * 0.15
            
            # 데이터베이스 관련 검증
            if any(word in text_content.lower() for word in ["database", "table", "schema", "sql"]):
                db_issues = self._validate_database_specifications(text_content)
                issues.extend(db_issues)
                score -= len(db_issues) * 0.15
        
        # 권장사항 생성
        if score < 0.8:
            recommendations.extend([
                "기술 명세의 정확성을 높이기 위해 표준 용어집 사용을 권장합니다",
                "API 명세는 OpenAPI 3.0 표준을 준수하는 것을 권장합니다",
                "데이터베이스 스키마는 정규화 원칙을 준수하는지 확인하세요"
            ])
        
        return max(0.0, score), issues, recommendations
    
    def _evaluate_implementation_feasibility(self, 
                                           criterion: ReviewCriterion, 
                                           content: Dict[str, Any], 
                                           review_result: ReviewResult) -> Tuple[float, List[ReviewIssue], List[str]]:
        """구현 가능성 평가"""
        
        issues = []
        recommendations = []
        score = 1.0
        
        if content.get("file_type") == "text":
            text_content = content.get("content", "")
            
            # 복잡도 분석
            complexity_indicators = [
                "real-time", "실시간", "high-performance", "고성능",
                "machine learning", "AI", "blockchain", "microservices"
            ]
            
            high_complexity_count = sum(1 for indicator in complexity_indicators 
                                      if indicator.lower() in text_content.lower())
            
            if high_complexity_count > 3:
                issues.append(ReviewIssue(
                    issue_id=f"impl_feas_001",
                    criterion_id=criterion.criterion_id,
                    severity=CriticalityLevel.HIGH,
                    title="구현 복잡도 높음",
                    description=f"고복잡도 요소 {high_complexity_count}개 감지",
                    location="전체 문서",
                    suggested_fix="복잡도를 낮추거나 단계적 구현 계획 수립",
                    blocking=False,
                    evidence=[f"복잡도 지표: {high_complexity_count}개"]
                ))
                score -= 0.3
            
            # 시간 제약 분석
            if "7일" in text_content or "1주" in text_content:
                word_count = content.get("word_count", 0)
                if word_count > 10000:  # 매우 긴 명세서
                    issues.append(ReviewIssue(
                        issue_id=f"impl_feas_002",
                        criterion_id=criterion.criterion_id,
                        severity=CriticalityLevel.HIGH,
                        title="시간 대비 범위 과다",
                        description="7일 일정 대비 명세 범위가 과도함",
                        location="전체 문서",
                        suggested_fix="핵심 기능 위주로 범위 축소 필요",
                        blocking=True,
                        evidence=[f"문서 길이: {word_count} 단어"]
                    ))
                    score -= 0.4
        
        return max(0.0, score), issues, recommendations
    
    def _evaluate_business_value(self, 
                               criterion: ReviewCriterion, 
                               content: Dict[str, Any], 
                               review_result: ReviewResult) -> Tuple[float, List[ReviewIssue], List[str]]:
        """비즈니스 가치 평가"""
        
        issues = []
        recommendations = []
        score = 1.0
        
        if content.get("file_type") == "text":
            text_content = content.get("content", "")
            
            # 비즈니스 가치 키워드 확인
            business_value_keywords = [
                "사용자", "고객", "효율성", "생산성", "ROI", "수익",
                "비용 절감", "경쟁력", "만족도", "가치"
            ]
            
            value_mentions = sum(1 for keyword in business_value_keywords 
                               if keyword in text_content)
            
            if value_mentions < 3:
                issues.append(ReviewIssue(
                    issue_id=f"biz_val_001",
                    criterion_id=criterion.criterion_id,
                    severity=CriticalityLevel.MEDIUM,
                    title="비즈니스 가치 언급 부족",
                    description="비즈니스 가치에 대한 명확한 언급이 부족함",
                    location="전체 문서",
                    suggested_fix="구체적인 비즈니스 가치와 측정 지표 추가",
                    blocking=False,
                    evidence=[f"가치 관련 언급: {value_mentions}회"]
                ))
                score -= 0.3
            
            # 사용자 중심성 확인
            user_focus_keywords = ["사용자", "고객", "user", "customer"]
            user_mentions = sum(text_content.lower().count(keyword.lower()) 
                              for keyword in user_focus_keywords)
            
            if user_mentions < 5:
                issues.append(ReviewIssue(
                    issue_id=f"biz_val_002",
                    criterion_id=criterion.criterion_id,
                    severity=CriticalityLevel.MEDIUM,
                    title="사용자 중심성 부족",
                    description="사용자 관점의 가치 언급이 부족함",
                    location="전체 문서",
                    suggested_fix="사용자 니즈와 가치 창출 방안 명시",
                    blocking=False,
                    evidence=[f"사용자 관련 언급: {user_mentions}회"]
                ))
                score -= 0.2
        
        return max(0.0, score), issues, recommendations
    
    def _evaluate_documentation_quality(self, 
                                      criterion: ReviewCriterion, 
                                      content: Dict[str, Any], 
                                      review_result: ReviewResult) -> Tuple[float, List[ReviewIssue], List[str]]:
        """문서화 품질 평가"""
        
        issues = []
        recommendations = []
        score = 1.0
        
        if content.get("file_type") == "text":
            sections = content.get("sections", [])
            text_content = content.get("content", "")
            
            # 구조 완성도 확인
            essential_sections = ["개요", "요구사항", "명세", "결론"]
            missing_sections = []
            
            for essential in essential_sections:
                if not any(essential in section for section in sections):
                    missing_sections.append(essential)
            
            if missing_sections:
                issues.append(ReviewIssue(
                    issue_id=f"doc_qual_001",
                    criterion_id=criterion.criterion_id,
                    severity=CriticalityLevel.MEDIUM,
                    title="필수 섹션 누락",
                    description=f"필수 섹션이 누락됨: {', '.join(missing_sections)}",
                    location="문서 구조",
                    suggested_fix="누락된 섹션을 추가하세요",
                    blocking=True,
                    evidence=missing_sections
                ))
                score -= len(missing_sections) * 0.2
            
            # 가독성 확인
            avg_sentence_length = self._calculate_average_sentence_length(text_content)
            if avg_sentence_length > 25:
                issues.append(ReviewIssue(
                    issue_id=f"doc_qual_002",
                    criterion_id=criterion.criterion_id,
                    severity=CriticalityLevel.LOW,
                    title="문장 길이 과다",
                    description=f"평균 문장 길이가 {avg_sentence_length:.1f}로 너무 김",
                    location="전체 문서",
                    suggested_fix="문장을 더 짧고 명확하게 작성하세요",
                    blocking=False,
                    evidence=[f"평균 문장 길이: {avg_sentence_length:.1f}"]
                ))
                score -= 0.1
        
        return max(0.0, score), issues, recommendations
    
    def _evaluate_consistency(self, 
                            criterion: ReviewCriterion, 
                            content: Dict[str, Any], 
                            review_result: ReviewResult) -> Tuple[float, List[ReviewIssue], List[str]]:
        """일관성 평가"""
        
        issues = []
        recommendations = []
        score = 1.0
        
        if content.get("file_type") == "text":
            text_content = content.get("content", "")
            
            # 용어 일관성 확인
            inconsistencies = self._check_term_consistency(text_content)
            
            for inconsistency in inconsistencies:
                issues.append(ReviewIssue(
                    issue_id=f"consist_001_{len(issues)}",
                    criterion_id=criterion.criterion_id,
                    severity=CriticalityLevel.LOW,
                    title=f"용어 불일치: {inconsistency['terms']}",
                    description="동일한 개념에 대해 다른 용어 사용",
                    location="전체 문서",
                    suggested_fix=f"'{inconsistency['recommended']}'로 통일",
                    blocking=False,
                    evidence=inconsistency['examples']
                ))
                score -= 0.05
        
        return max(0.0, score), issues, recommendations
    
    def _evaluate_generic_criterion(self, 
                                   criterion: ReviewCriterion, 
                                   content: Dict[str, Any], 
                                   review_result: ReviewResult) -> Tuple[float, List[ReviewIssue], List[str]]:
        """일반적 기준 평가"""
        
        issues = []
        recommendations = ["상세한 검토를 위해 전문가 리뷰를 권장합니다"]
        
        # 기본적인 완성도 평가
        if content.get("error"):
            score = 0.0
        elif content.get("word_count", 0) < 100:
            score = 0.3  # 너무 짧음
        else:
            score = 0.8  # 기본 점수
        
        return score, issues, recommendations
    
    def _make_approval_decision(self, review_result: ReviewResult) -> Dict[str, Any]:
        """승인/거부 결정"""
        
        # 블로킹 이슈 확인
        blocking_issues = [issue for issue in review_result.issues if issue.blocking]
        critical_issues = [issue for issue in review_result.issues 
                          if issue.severity == CriticalityLevel.CRITICAL]
        
        # 결정 로직
        if blocking_issues or critical_issues:
            status = ReviewStatus.REJECTED
            rationale = f"블로킹 이슈 {len(blocking_issues)}개, 치명적 이슈 {len(critical_issues)}개 발견"
            revision_required = True
        elif review_result.overall_score < 0.6:
            status = ReviewStatus.NEEDS_REVISION
            rationale = f"전체 점수 {review_result.overall_score:.2f}로 기준 미달 (최소 0.6 필요)"
            revision_required = True
        elif review_result.overall_score < 0.8:
            status = ReviewStatus.CONDITIONAL_APPROVAL
            rationale = f"조건부 승인 (점수: {review_result.overall_score:.2f})"
            revision_required = False
        else:
            status = ReviewStatus.APPROVED
            rationale = f"우수한 품질로 승인 (점수: {review_result.overall_score:.2f})"
            revision_required = False
        
        # 다음 리뷰어 결정
        next_reviewer = None
        if status == ReviewStatus.APPROVED and review_result.review_type != ReviewType.FINAL_APPROVAL:
            if review_result.review_type == ReviewType.TECHNICAL_REVIEW:
                next_reviewer = "product_owner"  # 기술 리뷰 후 비즈니스 리뷰
            elif review_result.review_type == ReviewType.BUSINESS_REVIEW:
                next_reviewer = "project_manager"  # 최종 승인
        
        return {
            "status": status,
            "rationale": rationale,
            "revision_required": revision_required,
            "next_reviewer": next_reviewer
        }
    
    def _send_review_request(self, review_result: ReviewResult, custom_criteria: List[str] = None):
        """리뷰 요청 메시지 전송"""
        
        # 리뷰 요청서 생성
        request_content = {
            "review_id": review_result.review_id,
            "type": "review_request",
            "deliverable_path": review_result.deliverable_path,
            "review_type": review_result.review_type.value,
            "urgency": "high",
            "criteria": [asdict(criterion) for criterion in 
                        self.review_criteria.get(review_result.review_type.value, [])],
            "custom_criteria": custom_criteria or [],
            "instructions": self._generate_review_instructions(review_result),
            "deadline": (datetime.now() + timedelta(hours=6)).isoformat()
        }
        
        # 통신 디렉토리에 요청 저장
        comm_dir = self.project_root / "communication" / f"to_{review_result.reviewer_role}"
        comm_dir.mkdir(parents=True, exist_ok=True)
        
        request_file = comm_dir / f"review_request_{review_result.review_id}.yaml"
        
        with open(request_file, 'w', encoding='utf-8') as f:
            yaml.dump(request_content, f, default_flow_style=False, allow_unicode=True)
        
        print(f"📧 리뷰 요청 전송: {review_result.reviewer_role} <- {review_result.review_id}")
    
    def _generate_review_instructions(self, review_result: ReviewResult) -> str:
        """리뷰 지시사항 생성"""
        
        instructions = f"""
# 리뷰 지시사항: {review_result.review_id}

## 🎯 리뷰 미션
당신은 **{review_result.reviewer_role}**로서 **{review_result.reviewee_role}**이 작성한 산출물을 **매우 엄격하고 이성적으로** 리뷰해야 합니다.

## 📋 리뷰 대상
- **파일**: {review_result.deliverable_path}
- **타입**: {review_result.review_type.value}
- **작성자**: {review_result.reviewee_role}

## 🔍 리뷰 원칙

### 1. 극도로 엄격한 기준 적용
- **완벽주의 접근**: 작은 결함도 놓치지 말 것
- **전문가 수준 검증**: 당신의 전문 영역에서 최고 수준 요구
- **AI 대 AI**: 인간의 감정적 배려 없이 순수 논리적 판단

### 2. 철저한 검증 프로세스
- **라인별 상세 검토**: 모든 내용을 꼼꼼히 분석
- **논리적 일관성**: 내용 간 모순이나 비논리적 부분 찾기
- **실현 가능성**: 제안된 내용의 실제 구현 가능성 엄격 평가

### 3. 건설적이지만 엄격한 피드백
- **구체적 지적**: 모호한 지적 금지, 정확한 위치와 이유 명시
- **개선 방안 제시**: 문제점과 함께 구체적 해결책 제공
- **우선순위 분류**: 치명적/중요/보통/경미로 이슈 분류

## 📊 평가 기준
리뷰 시스템이 자동으로 점수를 계산하지만, 당신의 전문적 판단이 최종 결정에 영향을 미칩니다.

## ⚡ 즉시 실행 사항
1. **파일 확인**: `cat {review_result.deliverable_path}`
2. **리뷰 수행**: `python3 ../../intelligent_review_system.py --conduct-review {review_result.review_id}`
3. **결과 확인**: 리뷰 결과를 검토하고 필요시 추가 의견 제시

## 🚨 중요 알림
- **승인 임계점**: 0.8점 이상만 무조건 승인
- **거부 기준**: 치명적 이슈 1개라도 발견 시 즉시 거부
- **재작업 요구**: 0.6점 미만은 반드시 재작업 요구

**지금 즉시 엄격한 리뷰를 시작하세요!** 🔍
"""
        
        return instructions
    
    def _notify_review_completion(self, review_result: ReviewResult):
        """리뷰 완료 통지"""
        
        # 작성자에게 리뷰 결과 통지
        notification = {
            "type": "review_completed",
            "review_id": review_result.review_id,
            "status": review_result.status.value,
            "overall_score": review_result.overall_score,
            "reviewer": review_result.reviewer_role,
            "issues_count": len(review_result.issues),
            "critical_issues": len([i for i in review_result.issues if i.severity == CriticalityLevel.CRITICAL]),
            "blocking_issues": len([i for i in review_result.issues if i.blocking]),
            "decision_rationale": review_result.decision_rationale,
            "revision_required": review_result.revision_required,
            "next_reviewer": review_result.next_reviewer,
            "recommendations": review_result.recommendations[:3],  # 상위 3개만
            "detailed_results_path": f"reviews/{review_result.review_id}.json"
        }
        
        # 작성자에게 통지
        comm_dir = self.project_root / "communication" / f"to_{review_result.reviewee_role}"
        comm_dir.mkdir(parents=True, exist_ok=True)
        
        notification_file = comm_dir / f"review_result_{review_result.review_id}.yaml"
        
        with open(notification_file, 'w', encoding='utf-8') as f:
            yaml.dump(notification, f, default_flow_style=False, allow_unicode=True)
        
        print(f"📬 리뷰 결과 통지: {review_result.reviewee_role} <- {review_result.status.value}")
    
    def _save_review_result(self, review_result: ReviewResult):
        """리뷰 결과 저장"""
        
        result_file = self.reviews_dir / f"{review_result.review_id}.json"
        
        # dataclass를 dict로 변환하면서 enum 처리
        result_dict = asdict(review_result)
        result_dict['review_type'] = review_result.review_type.value
        result_dict['status'] = review_result.status.value
        
        # 이슈들의 enum 값도 처리
        for issue in result_dict['issues']:
            issue['severity'] = issue['severity'] if isinstance(issue['severity'], str) else issue['severity'].value
        
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(result_dict, f, indent=2, ensure_ascii=False, default=str)
    
    # Helper methods for content analysis
    def _extract_markdown_sections(self, content: str) -> List[str]:
        """마크다운 섹션 추출"""
        import re
        sections = re.findall(r'^#+\s+(.+)$', content, re.MULTILINE)
        return sections
    
    def _analyze_json_structure(self, data: Any) -> Dict[str, Any]:
        """JSON 구조 분석"""
        def analyze_value(value):
            if isinstance(value, dict):
                return {"type": "object", "keys": len(value), "nested": True}
            elif isinstance(value, list):
                return {"type": "array", "length": len(value), "nested": len(value) > 0}
            else:
                return {"type": type(value).__name__, "nested": False}
        
        if isinstance(data, dict):
            return {key: analyze_value(value) for key, value in data.items()}
        return {"root": analyze_value(data)}
    
    def _analyze_yaml_structure(self, data: Any) -> Dict[str, Any]:
        """YAML 구조 분석"""
        return self._analyze_json_structure(data)  # JSON과 동일한 구조 분석
    
    def _check_technical_term_consistency(self, content: str, tech_terms: List[str]) -> List[Dict[str, Any]]:
        """기술 용어 일관성 확인"""
        inconsistencies = []
        
        for term in tech_terms:
            # 대소문자 다른 형태들 찾기
            import re
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            matches = pattern.findall(content)
            
            if len(set(matches)) > 1:  # 다른 형태로 사용됨
                inconsistencies.append({
                    "term": term,
                    "standard_form": term,
                    "variants": list(set(matches)),
                    "examples": matches[:3],
                    "lines": [i+1 for i, line in enumerate(content.splitlines()) 
                             if term.lower() in line.lower()][:3]
                })
        
        return inconsistencies
    
    def _validate_api_specifications(self, content: str) -> List[ReviewIssue]:
        """API 명세 검증"""
        issues = []
        
        # HTTP 메서드 확인
        http_methods = ["GET", "POST", "PUT", "DELETE", "PATCH"]
        found_methods = [method for method in http_methods if method in content]
        
        if not found_methods:
            issues.append(ReviewIssue(
                issue_id="api_val_001",
                criterion_id="tech_accuracy",
                severity=CriticalityLevel.MEDIUM,
                title="HTTP 메서드 누락",
                description="API 명세에 HTTP 메서드가 명시되지 않음",
                location="API 섹션",
                suggested_fix="GET, POST 등 HTTP 메서드 명시",
                blocking=False,
                evidence=[]
            ))
        
        # 엔드포인트 형식 확인
        import re
        endpoints = re.findall(r'/api/[^\s]+', content)
        for endpoint in endpoints:
            if not re.match(r'^/api/v\d+/', endpoint):
                issues.append(ReviewIssue(
                    issue_id=f"api_val_002_{len(issues)}",
                    criterion_id="tech_accuracy",
                    severity=CriticalityLevel.LOW,
                    title="API 버전 누락",
                    description=f"엔드포인트 {endpoint}에 버전 정보 누락",
                    location=f"엔드포인트: {endpoint}",
                    suggested_fix="/api/v1/ 형태로 버전 명시",
                    blocking=False,
                    evidence=[endpoint]
                ))
        
        return issues
    
    def _validate_database_specifications(self, content: str) -> List[ReviewIssue]:
        """데이터베이스 명세 검증"""
        issues = []
        
        # 기본 키 확인
        if "primary key" not in content.lower() and "pk" not in content.lower():
            issues.append(ReviewIssue(
                issue_id="db_val_001",
                criterion_id="tech_accuracy",
                severity=CriticalityLevel.HIGH,
                title="기본 키 누락",
                description="데이터베이스 테이블에 기본 키가 명시되지 않음",
                location="데이터베이스 섹션",
                suggested_fix="각 테이블에 기본 키 정의 추가",
                blocking=True,
                evidence=[]
            ))
        
        return issues
    
    def _check_term_consistency(self, content: str) -> List[Dict[str, Any]]:
        """용어 일관성 확인"""
        # 간단한 구현 - 실제로는 더 복잡한 NLP 분석 필요
        inconsistencies = []
        
        # 동의어 그룹들
        synonym_groups = [
            ["사용자", "유저", "user"],
            ["게시글", "포스트", "post"],
            ["댓글", "코멘트", "comment"],
            ["로그인", "signin", "sign-in"]
        ]
        
        for group in synonym_groups:
            found_terms = [term for term in group if term in content]
            if len(found_terms) > 1:
                inconsistencies.append({
                    "terms": found_terms,
                    "recommended": group[0],  # 첫 번째를 권장 용어로
                    "examples": found_terms[:2]
                })
        
        return inconsistencies
    
    def _calculate_average_sentence_length(self, content: str) -> float:
        """평균 문장 길이 계산"""
        sentences = content.split('.')
        sentences = [s.strip() for s in sentences if s.strip()]
        
        if not sentences:
            return 0.0
        
        total_words = sum(len(sentence.split()) for sentence in sentences)
        return total_words / len(sentences)

def main():
    """테스트 및 데모"""
    review_engine = IntelligentReviewEngine("/home/jungh/workspace/web_community_project")
    
    # 예시: 리뷰 요청
    review_id = review_engine.request_review(
        deliverable_path="roles/business_analyst/deliverables/business_requirements.md",
        reviewee_role="business_analyst",
        review_type=ReviewType.BUSINESS_REVIEW,
        priority=CriticalityLevel.HIGH
    )
    
    # 리뷰 수행
    result = review_engine.conduct_intelligent_review(review_id)
    
    print(f"✅ 리뷰 완료: {result.status.value} (점수: {result.overall_score:.2f})")
    print(f"📋 이슈 수: {len(result.issues)}")
    print(f"💡 권장사항: {len(result.recommendations)}")

if __name__ == "__main__":
    main()