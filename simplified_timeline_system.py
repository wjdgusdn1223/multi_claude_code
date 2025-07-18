#!/usr/bin/env python3
"""
Simplified Timeline System for Multi-Agent Claude Code
의미있는 순서 기반 간소화된 타임라인 시스템
"""

import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

class DependencyType(Enum):
    PREREQUISITE = "prerequisite"  # 필수 선행
    PARALLEL_OK = "parallel_ok"    # 병렬 가능
    SEQUENCE = "sequence"          # 순차 실행

@dataclass
class SimplePhase:
    """간소화된 단계"""
    phase_id: str
    name: str
    roles: List[str]
    key_outputs: List[str]
    dependency_type: DependencyType
    estimated_duration: str  # "1-2일", "반나절", "2-3시간" 등 의미있는 표현
    success_criteria: List[str]

class SimplifiedTimelineSystem:
    """간소화된 타임라인 시스템"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.timeline_dir = self.project_root / "timeline"
        self.timeline_dir.mkdir(exist_ok=True)
        
        # 간소화된 단계 정의
        self.phases = self._define_simplified_phases()
        
    def _define_simplified_phases(self) -> List[SimplePhase]:
        """간소화된 단계 정의"""
        
        return [
            SimplePhase(
                phase_id="P1_UNDERSTANDING",
                name="프로젝트 이해 및 계획",
                roles=["project_manager", "product_owner"],
                key_outputs=["프로젝트 개요", "초기 계획"],
                dependency_type=DependencyType.SEQUENCE,
                estimated_duration="반나절",
                success_criteria=["프로젝트 목표 명확화", "기본 계획 수립"]
            ),
            
            SimplePhase(
                phase_id="P2_REQUIREMENTS",
                name="요구사항 정의",
                roles=["business_analyst", "requirements_analyst"],
                key_outputs=["비즈니스 요구사항", "기술 요구사항"],
                dependency_type=DependencyType.SEQUENCE,
                estimated_duration="1일",
                success_criteria=["모든 요구사항 문서화", "이해관계자 승인"]
            ),
            
            SimplePhase(
                phase_id="P3_DESIGN",
                name="설계",
                roles=["system_architect", "ui_ux_designer", "database_designer"],
                key_outputs=["시스템 아키텍처", "UI 설계", "데이터 모델"],
                dependency_type=DependencyType.PARALLEL_OK,
                estimated_duration="1-2일",
                success_criteria=["설계 완료", "기술 검토 통과"]
            ),
            
            SimplePhase(
                phase_id="P4_DEVELOPMENT",
                name="개발",
                roles=["frontend_developer", "backend_developer", "fullstack_developer"],
                key_outputs=["프론트엔드 앱", "백엔드 API", "데이터베이스"],
                dependency_type=DependencyType.PARALLEL_OK,
                estimated_duration="2-3일",
                success_criteria=["모든 기능 구현", "단위 테스트 완료"]
            ),
            
            SimplePhase(
                phase_id="P5_TESTING",
                name="테스트 및 품질검증",
                roles=["qa_tester", "automation_tester", "performance_tester"],
                key_outputs=["테스트 결과", "품질 보고서"],
                dependency_type=DependencyType.PARALLEL_OK,
                estimated_duration="1일",
                success_criteria=["모든 테스트 통과", "품질 기준 달성"]
            ),
            
            SimplePhase(
                phase_id="P6_DEPLOYMENT",
                name="배포 및 운영준비",
                roles=["devops_engineer", "infrastructure_engineer", "sre_engineer"],
                key_outputs=["배포된 시스템", "운영 가이드"],
                dependency_type=DependencyType.SEQUENCE,
                estimated_duration="반나절",
                success_criteria=["성공적 배포", "운영 환경 준비"]
            )
        ]
    
    def generate_smart_timeline(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """지능적 타임라인 생성"""
        
        # 프로젝트 복잡도 분석
        complexity = self._assess_project_complexity(project_config)
        
        # 단계별 예상 시간 조정
        adjusted_phases = self._adjust_phase_durations(complexity)
        
        # 의존성 기반 실행 순서 계산
        execution_order = self._calculate_execution_order(adjusted_phases)
        
        # 전체 타임라인 생성
        timeline = {
            'project_name': project_config.get('project_name', 'Unknown'),
            'complexity_level': complexity['level'],
            'total_estimated_duration': self._calculate_total_duration(adjusted_phases),
            'execution_phases': execution_order,
            'critical_path': self._identify_critical_path(execution_order),
            'parallel_opportunities': self._identify_parallel_work(execution_order),
            'risk_factors': complexity['risk_factors'],
            'recommendations': self._generate_timeline_recommendations(complexity, execution_order)
        }
        
        return timeline
    
    def _assess_project_complexity(self, project_config: Dict[str, Any]) -> Dict[str, Any]:
        """프로젝트 복잡도 평가"""
        
        complexity_score = 0
        risk_factors = []
        
        # 기능 수 기반 복잡도
        features = project_config.get('features', [])
        if len(features) > 7:
            complexity_score += 2
            risk_factors.append("많은 기능 수")
        elif len(features) > 4:
            complexity_score += 1
        
        # 기술 스택 복잡도
        tech_stack = project_config.get('tech_stack', {})
        if len(tech_stack) > 3:
            complexity_score += 1
            risk_factors.append("복잡한 기술 스택")
        
        # 실시간 기능 여부
        description = project_config.get('description', '').lower()
        if any(word in description for word in ['실시간', 'real-time', '알림']):
            complexity_score += 2
            risk_factors.append("실시간 기능 요구")
        
        # 모바일 지원 여부
        if any(word in description for word in ['모바일', 'mobile', '반응형']):
            complexity_score += 1
            risk_factors.append("다중 플랫폼 지원")
        
        # 복잡도 레벨 결정
        if complexity_score >= 5:
            level = "high"
        elif complexity_score >= 3:
            level = "medium"
        else:
            level = "low"
        
        return {
            'score': complexity_score,
            'level': level,
            'risk_factors': risk_factors
        }
    
    def _adjust_phase_durations(self, complexity: Dict[str, Any]) -> List[Dict[str, Any]]:
        """복잡도에 따른 단계별 기간 조정"""
        
        adjusted_phases = []
        multiplier = {
            'low': 1.0,
            'medium': 1.3,
            'high': 1.6
        }[complexity['level']]
        
        for phase in self.phases:
            adjusted_phase = {
                'phase_id': phase.phase_id,
                'name': phase.name,
                'roles': phase.roles,
                'key_outputs': phase.key_outputs,
                'dependency_type': phase.dependency_type,
                'original_duration': phase.estimated_duration,
                'adjusted_duration': self._adjust_duration(phase.estimated_duration, multiplier),
                'success_criteria': phase.success_criteria,
                'complexity_impact': self._calculate_phase_complexity_impact(phase, complexity)
            }
            adjusted_phases.append(adjusted_phase)
        
        return adjusted_phases
    
    def _adjust_duration(self, original_duration: str, multiplier: float) -> str:
        """기간 조정"""
        
        duration_mapping = {
            "반나절": 0.5,
            "1일": 1.0,
            "1-2일": 1.5,
            "2-3일": 2.5,
            "2-3시간": 0.3
        }
        
        original_days = duration_mapping.get(original_duration, 1.0)
        adjusted_days = original_days * multiplier
        
        # 조정된 기간을 의미있는 표현으로 변환
        if adjusted_days <= 0.3:
            return "2-3시간"
        elif adjusted_days <= 0.5:
            return "반나절"
        elif adjusted_days <= 1.0:
            return "1일"
        elif adjusted_days <= 2.0:
            return "1-2일"
        elif adjusted_days <= 3.0:
            return "2-3일"
        else:
            return f"{int(adjusted_days)}일"
    
    def _calculate_execution_order(self, phases: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """실행 순서 계산"""
        
        execution_order = []
        
        for phase in phases:
            if phase['dependency_type'] == DependencyType.SEQUENCE:
                # 순차 실행 단계
                execution_order.append({
                    'phase': phase,
                    'execution_type': 'sequential',
                    'can_start_after': execution_order[-1]['phase']['phase_id'] if execution_order else None,
                    'estimated_start': self._calculate_start_time(execution_order),
                    'roles_needed': len(phase['roles'])
                })
            
            elif phase['dependency_type'] == DependencyType.PARALLEL_OK:
                # 병렬 실행 가능 단계
                execution_order.append({
                    'phase': phase,
                    'execution_type': 'parallel_possible',
                    'can_start_after': execution_order[-1]['phase']['phase_id'] if execution_order else None,
                    'estimated_start': self._calculate_start_time(execution_order),
                    'roles_needed': len(phase['roles']),
                    'parallel_groups': self._identify_parallel_groups(phase)
                })
        
        return execution_order
    
    def _calculate_start_time(self, existing_phases: List[Dict[str, Any]]) -> str:
        """시작 시간 계산"""
        if not existing_phases:
            return "즉시"
        
        last_phase = existing_phases[-1]
        if last_phase['execution_type'] == 'sequential':
            return f"{last_phase['phase']['name']} 완료 후"
        else:
            return f"{last_phase['phase']['name']}와 병렬 가능"
    
    def _identify_parallel_groups(self, phase: Dict[str, Any]) -> List[List[str]]:
        """병렬 작업 그룹 식별"""
        
        roles = phase['roles']
        
        # 역할별 병렬 그룹 정의
        parallel_mapping = {
            'design': ['system_architect', 'ui_ux_designer', 'database_designer'],
            'development': ['frontend_developer', 'backend_developer', 'fullstack_developer'],
            'testing': ['qa_tester', 'automation_tester', 'performance_tester'],
            'infrastructure': ['devops_engineer', 'infrastructure_engineer', 'sre_engineer']
        }
        
        groups = []
        for group_name, group_roles in parallel_mapping.items():
            intersection = list(set(roles) & set(group_roles))
            if intersection:
                groups.append(intersection)
        
        return groups
    
    def _calculate_total_duration(self, phases: List[Dict[str, Any]]) -> str:
        """전체 기간 계산"""
        
        duration_mapping = {
            "2-3시간": 0.3,
            "반나절": 0.5,
            "1일": 1.0,
            "1-2일": 1.5,
            "2-3일": 2.5
        }
        
        # 순차 실행 단계들의 기간 합계
        sequential_total = 0
        for phase in phases:
            if phase.get('execution_type') == 'sequential':
                duration = phase['adjusted_duration']
            else:
                duration = phase['adjusted_duration']
            
            sequential_total += duration_mapping.get(duration, 1.0)
        
        # 병렬 실행으로 인한 시간 단축 고려
        parallel_savings = sequential_total * 0.2  # 20% 시간 절약 가정
        
        total_days = max(1, sequential_total - parallel_savings)
        
        if total_days <= 1:
            return "1일"
        elif total_days <= 3:
            return "2-3일"
        elif total_days <= 5:
            return "4-5일"
        elif total_days <= 7:
            return "1주일"
        else:
            return f"{int(total_days)}일"
    
    def _identify_critical_path(self, execution_order: List[Dict[str, Any]]) -> List[str]:
        """임계 경로 식별"""
        
        critical_path = []
        
        for order in execution_order:
            phase = order['phase']
            
            # 순차 실행이거나 많은 역할이 필요한 단계를 임계 경로로 간주
            if (order['execution_type'] == 'sequential' or 
                order['roles_needed'] >= 3):
                critical_path.append(phase['name'])
        
        return critical_path
    
    def _identify_parallel_work(self, execution_order: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """병렬 작업 기회 식별"""
        
        parallel_opportunities = []
        
        for order in execution_order:
            if order['execution_type'] == 'parallel_possible':
                phase = order['phase']
                parallel_opportunities.append({
                    'phase_name': phase['name'],
                    'parallel_groups': order.get('parallel_groups', []),
                    'time_savings': "20-30% 시간 단축 가능",
                    'coordination_needed': len(order.get('parallel_groups', [])) > 1
                })
        
        return parallel_opportunities
    
    def _calculate_phase_complexity_impact(self, phase: SimplePhase, complexity: Dict[str, Any]) -> Dict[str, Any]:
        """단계별 복잡도 영향 계산"""
        
        impact = {
            'risk_level': 'low',
            'attention_needed': [],
            'mitigation_strategies': []
        }
        
        # 설계 단계에 대한 복잡도 영향
        if phase.phase_id == "P3_DESIGN" and complexity['level'] == 'high':
            impact['risk_level'] = 'high'
            impact['attention_needed'].extend([
                "아키텍처 복잡도 증가",
                "설계 검토 시간 증가"
            ])
            impact['mitigation_strategies'].extend([
                "전문가 리뷰 필수",
                "프로토타입 검증"
            ])
        
        # 개발 단계에 대한 복잡도 영향
        if phase.phase_id == "P4_DEVELOPMENT" and complexity['level'] in ['medium', 'high']:
            impact['risk_level'] = 'medium' if complexity['level'] == 'medium' else 'high'
            impact['attention_needed'].extend([
                "개발 복잡도 증가",
                "통합 이슈 가능성"
            ])
            impact['mitigation_strategies'].extend([
                "단계적 통합",
                "지속적 테스트"
            ])
        
        return impact
    
    def _generate_timeline_recommendations(self, complexity: Dict[str, Any], execution_order: List[Dict[str, Any]]) -> List[str]:
        """타임라인 권고사항 생성"""
        
        recommendations = []
        
        # 복잡도 기반 권고사항
        if complexity['level'] == 'high':
            recommendations.extend([
                "프로젝트 복잡도가 높아 단계적 접근을 권장합니다",
                "각 단계별 리뷰 포인트를 엄격히 준수하세요",
                "리스크 모니터링을 강화하세요"
            ])
        
        # 병렬 작업 권고사항
        parallel_phases = [order for order in execution_order if order['execution_type'] == 'parallel_possible']
        if len(parallel_phases) >= 2:
            recommendations.append("병렬 작업을 통해 전체 일정을 20-30% 단축할 수 있습니다")
        
        # 임계 경로 권고사항
        critical_path = self._identify_critical_path(execution_order)
        if len(critical_path) >= 3:
            recommendations.append(f"임계 경로 단계({', '.join(critical_path)})에 우선순위를 두세요")
        
        # 일반 권고사항
        recommendations.extend([
            "각 단계의 성공 기준을 명확히 정의하고 검증하세요",
            "정기적인 진행상황 점검으로 일정 지연을 방지하세요"
        ])
        
        return recommendations
    
    def create_simple_progress_tracker(self, timeline: Dict[str, Any]) -> Dict[str, Any]:
        """간단한 진행 추적기 생성"""
        
        tracker = {
            'project_name': timeline['project_name'],
            'current_phase': None,
            'completed_phases': [],
            'upcoming_phases': [phase['phase']['name'] for phase in timeline['execution_phases']],
            'overall_progress': 0,
            'next_milestones': [],
            'status_summary': "프로젝트 시작 준비"
        }
        
        # 다음 마일스톤 식별
        for phase_order in timeline['execution_phases'][:2]:  # 다음 2개 단계
            phase = phase_order['phase']
            tracker['next_milestones'].append({
                'phase_name': phase['name'],
                'key_outputs': phase['key_outputs'],
                'estimated_duration': phase['adjusted_duration'],
                'success_criteria': phase['success_criteria']
            })
        
        return tracker
    
    def save_simplified_timeline(self, timeline: Dict[str, Any]) -> str:
        """간소화된 타임라인 저장"""
        
        # 파일명 생성
        project_name = timeline['project_name'].replace(' ', '_').lower()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"timeline_{project_name}_{timestamp}.yaml"
        
        file_path = self.timeline_dir / filename
        
        # YAML 형태로 저장 (가독성 우선)
        with open(file_path, 'w', encoding='utf-8') as f:
            yaml.dump(timeline, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
        
        print(f"📅 간소화된 타임라인 저장: {file_path}")
        return str(file_path)

def main():
    """테스트 및 데모"""
    timeline_system = SimplifiedTimelineSystem("/home/jungh/workspace/multi_claude_code_sample")
    
    # 예시 프로젝트 설정
    project_config = {
        'project_name': 'Web Community Platform',
        'description': '사용자 간 소통을 위한 실시간 웹 커뮤니티 플랫폼',
        'features': [
            '사용자 인증',
            '게시판 기능',
            '댓글 시스템',
            '실시간 알림',
            '모바일 반응형',
            '관리자 패널'
        ],
        'tech_stack': {
            'frontend': 'React.js',
            'backend': 'Node.js',
            'database': 'PostgreSQL',
            'deployment': 'Docker + AWS'
        }
    }
    
    # 지능적 타임라인 생성
    timeline = timeline_system.generate_smart_timeline(project_config)
    
    print("🎯 생성된 타임라인:")
    print(f"  복잡도: {timeline['complexity_level']}")
    print(f"  전체 예상 기간: {timeline['total_estimated_duration']}")
    print(f"  임계 경로: {', '.join(timeline['critical_path'])}")
    print(f"  병렬 작업 기회: {len(timeline['parallel_opportunities'])}개")
    
    # 진행 추적기 생성
    tracker = timeline_system.create_simple_progress_tracker(timeline)
    
    # 타임라인 저장
    saved_file = timeline_system.save_simplified_timeline(timeline)
    
    print(f"✅ 타임라인 시스템 테스트 완료: {saved_file}")

if __name__ == "__main__":
    main()