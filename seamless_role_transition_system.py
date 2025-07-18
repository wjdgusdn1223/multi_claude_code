#!/usr/bin/env python3
"""
Seamless Role Transition System for Multi-Agent Claude Code
자동 역할 전환 및 완전 자율 워크플로우 시스템
"""

import os
import json
import yaml
import time
import signal
import threading
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import queue
import asyncio

class TransitionTrigger(Enum):
    """전환 트리거 타입"""
    TASK_COMPLETED = "task_completed"
    DELIVERABLE_READY = "deliverable_ready"
    DEPENDENCY_SATISFIED = "dependency_satisfied"
    APPROVAL_RECEIVED = "approval_received"
    TIME_BASED = "time_based"
    MANUAL_REQUEST = "manual_request"
    ERROR_ESCALATION = "error_escalation"
    COLLABORATION_NEEDED = "collaboration_needed"

class RoleState(Enum):
    """역할 상태"""
    INACTIVE = "inactive"
    INITIALIZING = "initializing"
    ACTIVE = "active"
    WAITING = "waiting"
    BLOCKED = "blocked"
    COMPLETED = "completed"
    SUSPENDED = "suspended"
    ERROR = "error"

@dataclass
class TransitionRule:
    """전환 규칙"""
    rule_id: str
    from_role: str
    to_role: str
    trigger: TransitionTrigger
    conditions: Dict[str, Any]
    priority: int
    auto_execute: bool
    preparation_commands: List[str]
    handoff_data: Dict[str, Any]
    timeout_seconds: Optional[int]

@dataclass
class RoleSession:
    """역할 세션 정보"""
    role_id: str
    session_id: str
    state: RoleState
    process_id: Optional[int]
    started_at: datetime
    last_activity: datetime
    completion_percentage: float
    current_task: str
    context: Dict[str, Any]
    accumulated_knowledge: Dict[str, Any]
    performance_metrics: Dict[str, Any]

class SeamlessTransitionEngine:
    """원활한 역할 전환 엔진"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.transition_dir = self.project_root / "transitions"
        self.session_dir = self.project_root / "sessions"
        
        # 디렉토리 생성
        self.transition_dir.mkdir(exist_ok=True)
        self.session_dir.mkdir(exist_ok=True)
        
        # 상태 관리
        self.active_sessions: Dict[str, RoleSession] = {}
        self.transition_rules: List[TransitionRule] = []
        self.transition_queue = queue.Queue()
        self.global_context: Dict[str, Any] = {}
        
        # 모니터링 스레드
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_transitions, daemon=True)
        self.event_handler_thread = threading.Thread(target=self._handle_transition_events, daemon=True)
        
        # 초기화
        self._initialize_transition_rules()
        self._load_global_context()
        
        # 스레드 시작
        self.monitor_thread.start()
        self.event_handler_thread.start()
        
        print("🔄 Seamless Role Transition Engine 시작됨")
    
    def _initialize_transition_rules(self):
        """기본 전환 규칙 초기화"""
        
        # 1. Project Manager -> Business Analyst
        self.transition_rules.append(TransitionRule(
            rule_id="pm_to_ba",
            from_role="project_manager",
            to_role="business_analyst",
            trigger=TransitionTrigger.DELIVERABLE_READY,
            conditions={
                "required_deliverables": ["project_plan.md", "timeline_schedule.md"],
                "completion_threshold": 75
            },
            priority=1,
            auto_execute=True,
            preparation_commands=[
                "validate_project_scope",
                "prepare_business_context",
                "notify_stakeholders"
            ],
            handoff_data={
                "project_context": "global",
                "stakeholder_requirements": "from_project_plan",
                "timeline_constraints": "from_schedule"
            },
            timeout_seconds=3600
        ))
        
        # 2. Business Analyst -> Requirements Analyst
        self.transition_rules.append(TransitionRule(
            rule_id="ba_to_ra",
            from_role="business_analyst",
            to_role="requirements_analyst",
            trigger=TransitionTrigger.DELIVERABLE_READY,
            conditions={
                "required_deliverables": ["business_requirements.md", "functional_specifications.md"],
                "approval_status": "approved_or_auto"
            },
            priority=1,
            auto_execute=True,
            preparation_commands=[
                "consolidate_business_knowledge",
                "prepare_technical_context",
                "validate_requirements_completeness"
            ],
            handoff_data={
                "business_requirements": "from_deliverables",
                "stakeholder_feedback": "from_communications",
                "priority_matrix": "auto_generated"
            },
            timeout_seconds=3600
        ))
        
        # 3. Requirements Analyst -> System Architect (병렬)
        self.transition_rules.append(TransitionRule(
            rule_id="ra_to_sa",
            from_role="requirements_analyst",
            to_role="system_architect",
            trigger=TransitionTrigger.DELIVERABLE_READY,
            conditions={
                "required_deliverables": ["technical_requirements.md", "system_specifications.md"],
                "technical_feasibility": "validated"
            },
            priority=1,
            auto_execute=True,
            preparation_commands=[
                "analyze_system_complexity",
                "identify_architecture_patterns",
                "prepare_design_context"
            ],
            handoff_data={
                "technical_requirements": "from_deliverables",
                "performance_requirements": "extracted",
                "integration_needs": "analyzed"
            },
            timeout_seconds=4800
        ))
        
        # 4. Requirements Analyst -> UX Researcher (병렬)
        self.transition_rules.append(TransitionRule(
            rule_id="ra_to_ux",
            from_role="requirements_analyst",
            to_role="ux_researcher",
            trigger=TransitionTrigger.COLLABORATION_NEEDED,
            conditions={
                "ui_requirements_present": True,
                "user_interaction_complexity": "medium_or_high"
            },
            priority=2,
            auto_execute=True,
            preparation_commands=[
                "extract_user_interaction_requirements",
                "prepare_user_research_scope"
            ],
            handoff_data={
                "user_requirements": "extracted_from_specs",
                "interaction_patterns": "identified"
            },
            timeout_seconds=2400
        ))
        
        # 5. System Architect -> Database Designer + Solution Architect (병렬)
        self.transition_rules.append(TransitionRule(
            rule_id="sa_to_db",
            from_role="system_architect",
            to_role="database_designer",
            trigger=TransitionTrigger.DELIVERABLE_READY,
            conditions={
                "required_deliverables": ["system_architecture.md"],
                "data_storage_needed": True
            },
            priority=1,
            auto_execute=True,
            preparation_commands=[
                "extract_data_requirements",
                "analyze_data_relationships"
            ],
            handoff_data={
                "data_model_requirements": "extracted",
                "performance_requirements": "inherited"
            },
            timeout_seconds=3600
        ))
        
        # 6. 개발 단계 시작 (여러 역할 동시)
        self.transition_rules.append(TransitionRule(
            rule_id="design_to_dev",
            from_role="solution_architect",
            to_role="backend_developer,frontend_developer",
            trigger=TransitionTrigger.DELIVERABLE_READY,
            conditions={
                "required_deliverables": ["solution_design.md", "api_specifications.md"],
                "database_schema_ready": True,
                "ui_designs_ready": True
            },
            priority=1,
            auto_execute=True,
            preparation_commands=[
                "setup_development_environment",
                "prepare_development_tasks",
                "coordinate_parallel_development"
            ],
            handoff_data={
                "development_specifications": "complete_set",
                "task_breakdown": "auto_generated",
                "coordination_plan": "parallel_dev_plan"
            },
            timeout_seconds=None  # 개발은 시간 제한 없음
        ))
    
    def register_role_session(self, role_id: str, process_id: Optional[int] = None) -> str:
        """역할 세션 등록"""
        session_id = f"{role_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        session = RoleSession(
            role_id=role_id,
            session_id=session_id,
            state=RoleState.INITIALIZING,
            process_id=process_id,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            completion_percentage=0.0,
            current_task="초기화",
            context={},
            accumulated_knowledge={},
            performance_metrics={}
        )
        
        self.active_sessions[session_id] = session
        self._save_session(session)
        
        print(f"🎭 역할 세션 등록: {role_id} (세션 ID: {session_id})")
        return session_id
    
    def update_role_progress(self, 
                           role_id: str, 
                           completion_percentage: float,
                           current_task: str = "",
                           context_updates: Dict[str, Any] = None,
                           deliverables_completed: List[str] = None):
        """역할 진행상황 업데이트"""
        
        session = self._get_active_session(role_id)
        if not session:
            print(f"⚠️ 활성 세션을 찾을 수 없습니다: {role_id}")
            return
        
        # 세션 업데이트
        session.completion_percentage = completion_percentage
        session.last_activity = datetime.now()
        
        if current_task:
            session.current_task = current_task
        
        if context_updates:
            session.context.update(context_updates)
        
        # 상태 변경
        if completion_percentage >= 100:
            session.state = RoleState.COMPLETED
        elif completion_percentage > 0:
            session.state = RoleState.ACTIVE
        
        # 산출물 완료 처리
        if deliverables_completed:
            self._handle_deliverables_completion(role_id, deliverables_completed)
        
        # 세션 저장
        self._save_session(session)
        
        # 전환 조건 확인
        self._check_transition_conditions(role_id)
        
        print(f"📊 {role_id} 진행률 업데이트: {completion_percentage}% - {current_task}")
    
    def trigger_manual_transition(self, 
                                from_role: str, 
                                to_role: str, 
                                reason: str = "manual_request") -> bool:
        """수동 역할 전환 트리거"""
        
        transition_event = {
            'type': 'manual_transition',
            'from_role': from_role,
            'to_role': to_role,
            'reason': reason,
            'timestamp': datetime.now().isoformat(),
            'manual': True
        }
        
        self.transition_queue.put(transition_event)
        print(f"🔄 수동 전환 요청: {from_role} -> {to_role}")
        return True
    
    def start_autonomous_workflow(self, 
                                initial_role: str = "project_manager",
                                project_config: Dict[str, Any] = None) -> bool:
        """자율 워크플로우 시작"""
        
        print(f"🚀 자율 워크플로우 시작: {initial_role}")
        
        # 프로젝트 컨텍스트 설정
        if project_config:
            self.global_context.update(project_config)
            self._save_global_context()
        
        # 초기 역할 시작
        return self._start_role_autonomously(initial_role, is_initial=True)
    
    def _start_role_autonomously(self, 
                               role_id: str, 
                               handoff_data: Dict[str, Any] = None,
                               is_initial: bool = False) -> bool:
        """역할을 자율적으로 시작"""
        
        try:
            role_dir = self.project_root / "roles" / role_id
            
            # 역할 디렉토리 확인
            if not role_dir.exists():
                print(f"❌ 역할 디렉토리가 존재하지 않습니다: {role_id}")
                return False
            
            # 기존 활성 세션 확인
            existing_session = self._get_active_session(role_id)
            if existing_session and existing_session.state == RoleState.ACTIVE:
                print(f"⚠️ {role_id}이 이미 활성 상태입니다")
                return True
            
            # 컨텍스트 전달 파일 생성
            if handoff_data or not is_initial:
                self._create_handoff_context(role_id, handoff_data or {})
            
            # 자율 역할 시작 스크립트 생성
            self._create_autonomous_start_script(role_id, is_initial)
            
            # Claude Code 프로세스 시작
            start_script = role_dir / "autonomous_start.sh"
            
            process = subprocess.Popen(
                ["/bin/bash", str(start_script)],
                cwd=str(role_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=os.setsid  # 프로세스 그룹 생성
            )
            
            # 세션 등록
            session_id = self.register_role_session(role_id, process.pid)
            
            # 초기 상태를 ACTIVE로 설정
            session = self.active_sessions[session_id]
            session.state = RoleState.ACTIVE
            self._save_session(session)
            
            print(f"✅ {role_id} 자율 시작 완료 (PID: {process.pid})")
            return True
            
        except Exception as e:
            print(f"❌ {role_id} 시작 실패: {str(e)}")
            return False
    
    def _create_handoff_context(self, role_id: str, handoff_data: Dict[str, Any]):
        """인계 컨텍스트 파일 생성"""
        
        context_file = self.project_root / "roles" / role_id / "handoff_context.json"
        
        handoff_context = {
            'timestamp': datetime.now().isoformat(),
            'global_context': self.global_context,
            'handoff_data': handoff_data,
            'project_status': self._get_project_status(),
            'active_roles': [session.role_id for session in self.active_sessions.values() 
                            if session.state == RoleState.ACTIVE],
            'available_deliverables': self._get_available_deliverables(),
            'pending_communications': self._get_pending_communications(role_id)
        }
        
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(handoff_context, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📋 {role_id}용 인계 컨텍스트 생성")
    
    def _create_autonomous_start_script(self, role_id: str, is_initial: bool):
        """자율 시작 스크립트 생성"""
        
        role_dir = self.project_root / "roles" / role_id
        script_file = role_dir / "autonomous_start.sh"
        
        # 초기 지시사항 생성
        if is_initial:
            initial_prompt = self._generate_initial_role_prompt(role_id)
        else:
            initial_prompt = self._generate_handoff_role_prompt(role_id)
        
        # Claude Code 시작 스크립트
        script_content = f'''#!/bin/bash

# {role_id} 자율 시작 스크립트
set -e

echo "🎭 {role_id} 자율 모드 시작"

# 작업 디렉토리 확인
cd "$(dirname "$0")"
pwd

# 필요한 디렉토리 생성
mkdir -p deliverables working docs

# 초기 지시사항 생성
cat > AUTONOMOUS_INSTRUCTIONS.md << 'EOF'
{initial_prompt}
EOF

# 진행상황 추적 스크립트 생성
cat > track_progress.py << 'EOF'
#!/usr/bin/env python3
import sys
import json
import requests
from datetime import datetime

def update_progress(percentage, task, deliverables=None):
    progress_data = {{
        'role_id': '{role_id}',
        'timestamp': datetime.now().isoformat(),
        'completion_percentage': percentage,
        'current_task': task,
        'deliverables_completed': deliverables or []
    }}
    
    # 진행상황을 파일로 저장
    with open('progress_status.json', 'w') as f:
        json.dump(progress_data, f, indent=2)
    
    print(f"📊 진행률 업데이트: {{percentage}}% - {{task}}")

if __name__ == "__main__":
    if len(sys.argv) >= 3:
        percentage = float(sys.argv[1])
        task = sys.argv[2]
        deliverables = sys.argv[3:] if len(sys.argv) > 3 else None
        update_progress(percentage, task, deliverables)
EOF

chmod +x track_progress.py

# 상태 모니터링 스크립트 (백그라운드)
(
    while true; do
        if [ -f "progress_status.json" ]; then
            # 진행상황을 전환 엔진에 전달
            python3 - << 'PYEOF'
import json
import sys
import os
sys.path.append('{str(self.project_root)}')

try:
    with open('progress_status.json', 'r') as f:
        progress = json.load(f)
    
    # 전환 엔진 상태 파일에 기록
    transition_status_file = '{str(self.transition_dir)}/role_status_{role_id}.json'
    with open(transition_status_file, 'w') as f:
        json.dump(progress, f, indent=2)
        
    print(f"Status updated for {role_id}")
except Exception as e:
    print(f"Status update failed: {{e}}")
PYEOF
        fi
        sleep 30
    done
) &

# Claude Code 시작
echo "🤖 Claude Code 시작 중..."
claude-code --resume

# 완료 시 정리
echo "✅ {role_id} 작업 완료"
python3 track_progress.py 100 "작업 완료"
'''
        
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # 실행 권한 부여
        script_file.chmod(0o755)
        
        print(f"📝 {role_id}용 자율 시작 스크립트 생성")
    
    def _generate_initial_role_prompt(self, role_id: str) -> str:
        """초기 역할 프롬프트 생성"""
        
        role_config = self._get_role_config(role_id)
        
        prompt = f'''
# {role_config.get('role_name', role_id)} 자율 모드 지시사항

## 🎯 미션
당신은 **완전 자율 멀티 에이전트 시스템**의 {role_config.get('role_name')}입니다.
**인간의 개입 없이** 프로젝트를 성공적으로 완료하는 것이 목표입니다.

## 🔄 자율 모드 특별 지침

### 1. 능동적 작업 수행
- 주어진 책임사항을 **스스로 판단하여** 수행
- 불명확한 사항은 **다른 역할에게 적극적으로 질문**
- 의존성이 충족되는 즉시 **자동으로 다음 작업 시작**

### 2. 지능적 의사결정
- 비즈니스 가치와 프로젝트 목표를 고려한 의사결정
- 리스크가 있는 결정은 **관련 역할과 협의**
- 중요한 결정사항은 **문서화하여 공유**

### 3. 실시간 진행상황 보고
- 작업 진행률을 **실시간으로 업데이트**: `python3 track_progress.py <퍼센트> "<현재작업>"`
- 산출물 완료 시: `python3 track_progress.py <퍼센트> "<작업명>" <산출물파일명>`
- **5분마다** 진행상황 업데이트 필수

### 4. 자동 품질 관리
- 모든 산출물은 **자체 검토 후** 제출
- 다른 역할의 **리뷰 요청을 적극적으로** 보내기
- 품질 기준 미달 시 **자동으로 재작업**

## 📋 현재 역할 정보
- **역할**: {role_config.get('role_name')}
- **주요 책임**: {', '.join(role_config.get('responsibilities', []))}
- **필수 산출물**: {', '.join(role_config.get('deliverables', []))}
- **협업 대상**: {', '.join(role_config.get('collaborates_with', []))}

## 🚀 시작 절차
1. **현재 상황 파악**: `cat handoff_context.json` (있는 경우)
2. **의존성 확인**: 필요한 입력물들이 준비되었는지 체크
3. **작업 계획 수립**: 구체적이고 실행 가능한 작업 계획
4. **진행률 보고**: `python3 track_progress.py 10 "작업 계획 수립 완료"`
5. **작업 시작**: 첫 번째 작업 즉시 시작

## 🤝 협업 가이드
- **질문하기**: 불분명한 사항은 즉시 관련 역할에게 메시지 전송
- **피드백 요청**: 중요한 결정이나 산출물은 반드시 피드백 요청
- **상황 공유**: 블로커나 지연 요소 발견 시 즉시 공유
- **지식 공유**: 유용한 인사이트 발견 시 다른 역할들과 공유

## ⚡ 자동화 활용
- **모듈형 문서**: 큰 문서는 기능별로 나누어 작성
- **템플릿 사용**: 표준 템플릿을 활용한 빠른 문서 작성
- **자동 검증**: 체크리스트를 활용한 품질 검증

## 🎯 성공 기준
- **100% 완료**: 모든 필수 산출물 완료
- **품질 보증**: 동료 검토 통과
- **적시 전달**: 다음 역할이 즉시 작업 시작 가능한 상태로 전달
- **지식 축적**: 프로젝트 전체에 도움이 되는 인사이트 제공

지금 즉시 작업을 시작하세요! 🚀
'''
        
        return prompt
    
    def _generate_handoff_role_prompt(self, role_id: str) -> str:
        """인계 역할 프롬프트 생성"""
        
        role_config = self._get_role_config(role_id)
        
        prompt = f'''
# {role_config.get('role_name', role_id)} 인계 시작 지시사항

## 🔄 인계 받은 작업
이전 역할로부터 작업이 인계되었습니다. **즉시 작업을 시작**하세요.

### 📋 인계 정보 확인
1. **인계 컨텍스트**: `cat handoff_context.json`에서 상세 정보 확인
2. **이전 산출물**: 의존성 있는 산출물들 검토
3. **프로젝트 상황**: 전체 프로젝트 진행 상황 파악

### 🎯 우선 작업 절차
1. **상황 파악** (5분): 인계받은 정보와 현재 프로젝트 상태 분석
2. **진행률 보고**: `python3 track_progress.py 5 "인계 받아 상황 분석 중"`
3. **작업 계획**: 구체적인 실행 계획 수립
4. **즉시 시작**: 첫 번째 작업 바로 시작

## 🚀 자율 모드 활성화
**완전 자율 모드**에서 작업합니다:
- 인간 개입 없이 모든 결정
- 다른 역할과의 능동적 협업
- 실시간 진행상황 보고 (5분마다)
- 품질 기준 달성 시까지 자동 재작업

## 📊 필수 보고 사항
- **즉시**: `python3 track_progress.py 10 "인계 완료, 작업 시작"`
- **30분 후**: `python3 track_progress.py 25 "첫 번째 마일스톤 완료"`
- **산출물 완료 시**: `python3 track_progress.py <퍼센트> "산출물 완료" <파일명>`

인계받은 작업을 **지금 즉시 시작**하세요! ⚡
'''
        
        return prompt
    
    def _monitor_transitions(self):
        """전환 모니터링 (백그라운드)"""
        
        while self.monitoring_active:
            try:
                # 각 역할의 상태 파일 확인
                for status_file in self.transition_dir.glob("role_status_*.json"):
                    try:
                        with open(status_file, 'r', encoding='utf-8') as f:
                            status = json.load(f)
                        
                        role_id = status.get('role_id')
                        if role_id:
                            # 진행상황 업데이트
                            self.update_role_progress(
                                role_id=role_id,
                                completion_percentage=status.get('completion_percentage', 0),
                                current_task=status.get('current_task', ''),
                                deliverables_completed=status.get('deliverables_completed', [])
                            )
                        
                        # 처리된 상태 파일 삭제
                        status_file.unlink()
                        
                    except Exception as e:
                        print(f"⚠️ 상태 파일 처리 오류 ({status_file}): {str(e)}")
                
                # 세션 타임아웃 확인
                self._check_session_timeouts()
                
                time.sleep(10)  # 10초마다 확인
                
            except Exception as e:
                print(f"⚠️ 전환 모니터링 오류: {str(e)}")
                time.sleep(30)
    
    def _handle_transition_events(self):
        """전환 이벤트 처리 (백그라운드)"""
        
        while self.monitoring_active:
            try:
                # 전환 큐에서 이벤트 가져오기
                event = self.transition_queue.get(timeout=5)
                
                if event:
                    self._process_transition_event(event)
                
            except queue.Empty:
                continue
            except Exception as e:
                print(f"⚠️ 전환 이벤트 처리 오류: {str(e)}")
    
    def _process_transition_event(self, event: Dict[str, Any]):
        """전환 이벤트 처리"""
        
        event_type = event.get('type')
        
        if event_type == 'manual_transition':
            self._execute_manual_transition(event)
        elif event_type == 'auto_transition':
            self._execute_auto_transition(event)
        elif event_type == 'deliverable_completed':
            self._handle_deliverable_completion_event(event)
        else:
            print(f"⚠️ 알 수 없는 전환 이벤트: {event_type}")
    
    def _execute_auto_transition(self, event: Dict[str, Any]):
        """자동 전환 실행"""
        
        from_role = event.get('from_role')
        to_roles = event.get('to_roles', [])
        handoff_data = event.get('handoff_data', {})
        
        print(f"🔄 자동 전환 실행: {from_role} -> {to_roles}")
        
        # 이전 역할 세션 완료 처리
        if from_role:
            session = self._get_active_session(from_role)
            if session:
                session.state = RoleState.COMPLETED
                session.completion_percentage = 100.0
                self._save_session(session)
        
        # 새 역할들 시작
        for to_role in to_roles:
            success = self._start_role_autonomously(to_role, handoff_data)
            if success:
                print(f"✅ {to_role} 자동 시작 성공")
            else:
                print(f"❌ {to_role} 자동 시작 실패")
    
    def _execute_manual_transition(self, event: Dict[str, Any]):
        """수동 전환 실행"""
        
        from_role = event.get('from_role')
        to_role = event.get('to_role')
        
        print(f"🔄 수동 전환 실행: {from_role} -> {to_role}")
        
        # 간단한 수동 전환 (실제로는 더 복잡한 로직 필요)
        success = self._start_role_autonomously(to_role)
        
        if success:
            print(f"✅ 수동 전환 성공: {to_role}")
        else:
            print(f"❌ 수동 전환 실패: {to_role}")
    
    def _check_transition_conditions(self, role_id: str):
        """전환 조건 확인"""
        
        session = self._get_active_session(role_id)
        if not session:
            return
        
        # 완료된 역할에 대한 전환 규칙 확인
        if session.state == RoleState.COMPLETED:
            applicable_rules = [
                rule for rule in self.transition_rules
                if rule.from_role == role_id and rule.auto_execute
            ]
            
            for rule in applicable_rules:
                if self._evaluate_transition_conditions(rule, session):
                    self._trigger_auto_transition(rule, session)
    
    def _evaluate_transition_conditions(self, rule: TransitionRule, session: RoleSession) -> bool:
        """전환 조건 평가"""
        
        conditions = rule.conditions
        
        # 완료율 조건
        if 'completion_threshold' in conditions:
            if session.completion_percentage < conditions['completion_threshold']:
                return False
        
        # 필수 산출물 조건
        if 'required_deliverables' in conditions:
            available_deliverables = self._get_available_deliverables()
            required = conditions['required_deliverables']
            
            for deliverable in required:
                if not any(deliverable in path for path in available_deliverables):
                    return False
        
        # 승인 상태 조건
        if 'approval_status' in conditions:
            # 승인 상태 확인 로직 (간단화)
            if conditions['approval_status'] == 'approved_or_auto':
                return True  # 자동 승인
        
        return True
    
    def _trigger_auto_transition(self, rule: TransitionRule, from_session: RoleSession):
        """자동 전환 트리거"""
        
        # 인계 데이터 준비
        handoff_data = self._prepare_handoff_data(rule, from_session)
        
        # 대상 역할들 (쉼표로 구분된 경우 분리)
        to_roles = rule.to_role.split(',') if ',' in rule.to_role else [rule.to_role]
        
        # 전환 이벤트 생성
        transition_event = {
            'type': 'auto_transition',
            'rule_id': rule.rule_id,
            'from_role': rule.from_role,
            'to_roles': to_roles,
            'handoff_data': handoff_data,
            'timestamp': datetime.now().isoformat()
        }
        
        self.transition_queue.put(transition_event)
        print(f"🎯 자동 전환 트리거: {rule.from_role} -> {to_roles}")
    
    def _prepare_handoff_data(self, rule: TransitionRule, from_session: RoleSession) -> Dict[str, Any]:
        """인계 데이터 준비"""
        
        handoff_data = {}
        
        for key, source in rule.handoff_data.items():
            if source == "global":
                handoff_data[key] = self.global_context
            elif source == "from_deliverables":
                handoff_data[key] = self._get_role_deliverables(from_session.role_id)
            elif source == "from_communications":
                handoff_data[key] = self._get_role_communications(from_session.role_id)
            elif source.startswith("auto_generated"):
                handoff_data[key] = self._auto_generate_handoff_data(source, from_session)
        
        return handoff_data
    
    def _handle_deliverables_completion(self, role_id: str, deliverables: List[str]):
        """산출물 완료 처리"""
        
        for deliverable in deliverables:
            # 산출물 완료 이벤트 생성
            event = {
                'type': 'deliverable_completed',
                'role_id': role_id,
                'deliverable': deliverable,
                'timestamp': datetime.now().isoformat()
            }
            
            self.transition_queue.put(event)
            print(f"📄 산출물 완료: {role_id} - {deliverable}")
    
    # Helper methods
    def _get_active_session(self, role_id: str) -> Optional[RoleSession]:
        """활성 세션 조회"""
        for session in self.active_sessions.values():
            if session.role_id == role_id and session.state in [RoleState.ACTIVE, RoleState.WAITING]:
                return session
        return None
    
    def _get_role_config(self, role_id: str) -> Dict[str, Any]:
        """역할 설정 조회"""
        roles_file = self.project_root / "roles.yaml"
        if roles_file.exists():
            with open(roles_file, 'r', encoding='utf-8') as f:
                roles_config = yaml.safe_load(f)
            return roles_config.get('roles', {}).get(role_id, {})
        return {}
    
    def _save_session(self, session: RoleSession):
        """세션 저장"""
        session_file = self.session_dir / f"{session.session_id}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(session), f, indent=2, ensure_ascii=False, default=str)
    
    def _load_global_context(self):
        """글로벌 컨텍스트 로드"""
        context_file = self.project_root / "global_context.json"
        if context_file.exists():
            with open(context_file, 'r', encoding='utf-8') as f:
                self.global_context = json.load(f)
    
    def _save_global_context(self):
        """글로벌 컨텍스트 저장"""
        context_file = self.project_root / "global_context.json"
        with open(context_file, 'w', encoding='utf-8') as f:
            json.dump(self.global_context, f, indent=2, ensure_ascii=False, default=str)
    
    def _get_project_status(self) -> Dict[str, Any]:
        """프로젝트 상태 조회"""
        return {
            'active_sessions': len([s for s in self.active_sessions.values() if s.state == RoleState.ACTIVE]),
            'completed_sessions': len([s for s in self.active_sessions.values() if s.state == RoleState.COMPLETED]),
            'overall_progress': self._calculate_overall_progress()
        }
    
    def _calculate_overall_progress(self) -> float:
        """전체 진행률 계산"""
        if not self.active_sessions:
            return 0.0
        
        total_progress = sum(session.completion_percentage for session in self.active_sessions.values())
        return total_progress / len(self.active_sessions)
    
    def _get_available_deliverables(self) -> List[str]:
        """사용 가능한 산출물 목록"""
        deliverables = []
        
        for role_dir in (self.project_root / "roles").glob("*/deliverables"):
            if role_dir.is_dir():
                for file in role_dir.glob("*"):
                    if file.is_file():
                        deliverables.append(str(file.relative_to(self.project_root)))
        
        return deliverables
    
    def _get_pending_communications(self, role_id: str) -> List[Dict[str, Any]]:
        """대기 중인 통신 메시지"""
        comm_dir = self.project_root / "communication" / f"to_{role_id}"
        messages = []
        
        if comm_dir.exists():
            for msg_file in comm_dir.glob("*.yaml"):
                try:
                    with open(msg_file, 'r', encoding='utf-8') as f:
                        message = yaml.safe_load(f)
                    messages.append(message)
                except Exception:
                    pass
        
        return messages
    
    def _get_role_deliverables(self, role_id: str) -> List[str]:
        """역할별 산출물 조회"""
        deliverables_dir = self.project_root / "roles" / role_id / "deliverables"
        deliverables = []
        
        if deliverables_dir.exists():
            for file in deliverables_dir.glob("*"):
                if file.is_file():
                    deliverables.append(str(file))
        
        return deliverables
    
    def _get_role_communications(self, role_id: str) -> List[Dict[str, Any]]:
        """역할별 통신 내역 조회"""
        # 간단한 구현
        return []
    
    def _auto_generate_handoff_data(self, source: str, session: RoleSession) -> Any:
        """자동 인계 데이터 생성"""
        if source == "auto_generated":
            return {
                'session_summary': f"{session.role_id} 세션 요약",
                'key_decisions': session.accumulated_knowledge.get('decisions', []),
                'recommendations': session.accumulated_knowledge.get('recommendations', [])
            }
        return {}
    
    def _check_session_timeouts(self):
        """세션 타임아웃 확인"""
        current_time = datetime.now()
        
        for session in list(self.active_sessions.values()):
            if session.state == RoleState.ACTIVE:
                inactive_duration = current_time - session.last_activity
                
                # 2시간 이상 비활성 시 경고
                if inactive_duration > timedelta(hours=2):
                    print(f"⚠️ {session.role_id} 세션 장시간 비활성: {inactive_duration}")
                    
                    # 4시간 이상 비활성 시 타임아웃
                    if inactive_duration > timedelta(hours=4):
                        session.state = RoleState.ERROR
                        self._save_session(session)
                        print(f"❌ {session.role_id} 세션 타임아웃")

    def shutdown(self):
        """시스템 종료"""
        print("🛑 Seamless Transition Engine 종료 중...")
        
        self.monitoring_active = False
        
        # 활성 세션들 정리
        for session in self.active_sessions.values():
            if session.process_id:
                try:
                    os.killpg(os.getpgid(session.process_id), signal.SIGTERM)
                except:
                    pass
        
        print("✅ 시스템 종료 완료")

def main():
    """테스트 및 데모"""
    import signal
    import sys
    
    # 전환 엔진 시작
    engine = SeamlessTransitionEngine("/home/jungh/workspace/web_community_project")
    
    # 종료 시그널 핸들러
    def signal_handler(sig, frame):
        engine.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 자율 워크플로우 시작
    project_config = {
        'project_name': 'Web Community Platform',
        'start_time': datetime.now().isoformat(),
        'target_completion': '2025-07-24',
        'priority': 'high'
    }
    
    engine.start_autonomous_workflow(
        initial_role="project_manager",
        project_config=project_config
    )
    
    print("🚀 자율 워크플로우가 시작되었습니다.")
    print("Ctrl+C로 종료하세요.")
    
    # 메인 루프
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        engine.shutdown()

if __name__ == "__main__":
    main()