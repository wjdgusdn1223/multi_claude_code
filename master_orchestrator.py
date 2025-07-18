#!/usr/bin/env python3
"""
Master Orchestrator System for Multi-Agent Claude Code
통합 마스터 오케스트레이터 - 모든 역할과 도구를 관리하는 중앙 제어 시스템
"""

import os
import json
import yaml
import subprocess
import threading
import time
import signal
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
from dataclasses import dataclass, asdict
import sqlite3
import queue
import logging
from flask import Flask, render_template, jsonify, request, send_file
from flask_socketio import SocketIO, emit
import uuid

# 기존 시스템들 import
from enhanced_communication_system import ActiveCommunicationEngine, SmartMessage, MessageType
from intelligent_review_system import IntelligentReviewEngine, ReviewType

# 채팅 메시지 데이터 구조
@dataclass
class ChatMessage:
    message_id: str
    sender: str  # 'user' 또는 role_id
    receiver: str  # 'user' 또는 role_id
    content: str
    timestamp: datetime
    message_type: str = "text"  # text, command, response, approval_request
    processed: bool = False

# 명령어 승인 요청 데이터 구조
@dataclass
class CommandApprovalRequest:
    request_id: str
    role_id: str
    command: str
    description: str
    tool_name: str
    parameters: Dict[str, Any]
    timestamp: datetime
    approved: Optional[bool] = None
    user_response: Optional[str] = None
from context_persistence_system import ContextPersistenceSystem, ContextType
from smart_file_discovery_system import SmartFileDiscoverySystem, SearchQuery, FileType
from document_tracking_system import DocumentTrackingSystem
from modular_document_templates import ModularDocumentSystem
from ai_optimized_deliverable_templates import AIOptimizedDeliverableSystem

class ProjectPhase(Enum):
    """프로젝트 단계"""
    PLANNING = "planning"
    REQUIREMENTS = "requirements"
    DESIGN = "design"
    DEVELOPMENT = "development"
    TESTING = "testing"
    DEPLOYMENT = "deployment"
    MAINTENANCE = "maintenance"
    ROLLBACK = "rollback"

class RoleInstanceStatus(Enum):
    """역할 인스턴스 상태"""
    STOPPED = "stopped"
    STARTING = "starting"
    ACTIVE = "active"
    BUSY = "busy"
    WAITING_APPROVAL = "waiting_approval"
    ERROR = "error"
    STOPPING = "stopping"

class DecisionLevel(Enum):
    """결정 중요도"""
    AUTO = "auto"           # AI 자동 결정
    NOTIFY = "notify"       # AI 결정 후 사용자 알림
    APPROVAL = "approval"   # 사용자 승인 필요
    CRITICAL = "critical"   # 중요한 사용자 결정

@dataclass
class RoleInstance:
    """역할 인스턴스"""
    role_id: str
    role_name: str
    process: Optional[subprocess.Popen]
    status: RoleInstanceStatus
    current_task: Optional[str]
    work_directory: str
    log_file: str
    start_time: Optional[datetime]
    last_activity: Optional[datetime]
    performance_score: float
    error_count: int
    
@dataclass
class UserDecision:
    """사용자 결정 요청"""
    decision_id: str
    level: DecisionLevel
    title: str
    description: str
    options: List[Dict[str, Any]]
    requesting_role: str
    context: Dict[str, Any]
    created_at: datetime
    deadline: Optional[datetime]
    resolved: bool
    user_response: Optional[Dict[str, Any]]

@dataclass
class WorkflowStep:
    """워크플로우 단계"""
    step_id: str
    phase: ProjectPhase
    roles_required: List[str]
    dependencies: List[str]
    can_rollback_to: List[str]
    auto_transition: bool
    approval_required: bool
    estimated_duration: str
    success_criteria: List[str]

@dataclass
class RoleCommunication:
    """역할 간 소통 기록"""
    communication_id: str
    from_role: str
    to_role: str
    message: str
    message_type: str
    timestamp: datetime
    processed: bool = False

class MasterOrchestrator:
    """마스터 오케스트레이터 - 모든 시스템의 중앙 제어"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()  # 절대 경로로 변환
        self.master_dir = self.project_root / "master_orchestrator"
        self.logs_dir = self.master_dir / "logs"
        self.decisions_dir = self.master_dir / "decisions"
        self.workflows_dir = self.master_dir / "workflows"
        
        # 디렉토리 생성
        for directory in [self.master_dir, self.logs_dir, self.decisions_dir, self.workflows_dir]:
            directory.mkdir(exist_ok=True)
        
        # 데이터베이스 초기화
        self.db_path = self.master_dir / "orchestrator.db"
        self._init_database()
        
        # 하위 시스템들 초기화
        self.communication_engine = ActiveCommunicationEngine(str(self.project_root))
        self.review_engine = IntelligentReviewEngine(str(self.project_root))
        self.context_system = ContextPersistenceSystem(str(self.project_root))
        self.file_discovery = SmartFileDiscoverySystem(str(self.project_root))
        self.document_tracking = DocumentTrackingSystem(str(self.project_root))
        self.modular_docs = ModularDocumentSystem(str(self.project_root))
        self.ai_templates = AIOptimizedDeliverableSystem(str(self.project_root))
        
        # 상태 관리
        self.role_instances: Dict[str, RoleInstance] = {}
        self.current_phase = ProjectPhase.PLANNING
        self.workflow_active = False
        self.pending_decisions: Dict[str, UserDecision] = {}
        self.project_config: Dict[str, Any] = {}
        
        # 통신 큐
        self.message_queue = queue.Queue()
        self.decision_queue = queue.Queue()
        
        # 웹 UI 설정
        self.app = Flask(__name__, 
                        template_folder=str(self.master_dir / "templates"),
                        static_folder=str(self.master_dir / "static"))
        self.app.config['SECRET_KEY'] = 'master_orchestrator_key'
        self.socketio = SocketIO(self.app, cors_allowed_origins="*")
        
        # 로깅 설정
        self.logger = self._setup_logging()
        
        # 역할 정의
        self.available_roles = self._define_roles()
        
        # 워크플로우 정의
        self.workflow_steps = self._define_workflow()
        
        # 채팅 시스템
        self.chat_messages = []  # 모든 채팅 메시지 저장
        self.command_approval_requests = {}  # 승인 대기 중인 명령어들
        self.message_queue = queue.Queue()  # 메시지 큐
        
        # 역할 간 소통 기록
        self.role_communications = []
        
        # 백그라운드 스레드들
        self.orchestration_active = True
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.communication_thread = threading.Thread(target=self._communication_loop, daemon=True)
        self.decision_thread = threading.Thread(target=self._decision_loop, daemon=True)
        self.chat_thread = threading.Thread(target=self._chat_processing_loop, daemon=True)
        
        # 웹 라우트 설정
        self._setup_web_routes()
        
        # UI 템플릿 생성
        self._create_ui_templates()
        
        print("🎯 Master Orchestrator 시스템 초기화 완료")
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            # 역할 인스턴스 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS role_instances (
                    role_id TEXT PRIMARY KEY,
                    role_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    current_task TEXT,
                    work_directory TEXT NOT NULL,
                    log_file TEXT NOT NULL,
                    start_time TEXT,
                    last_activity TEXT,
                    performance_score REAL DEFAULT 0.5,
                    error_count INTEGER DEFAULT 0,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            # 사용자 결정 테이블
            conn.execute('''
                CREATE TABLE IF NOT EXISTS user_decisions (
                    decision_id TEXT PRIMARY KEY,
                    level TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    options TEXT NOT NULL,
                    requesting_role TEXT NOT NULL,
                    context TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    deadline TEXT,
                    resolved BOOLEAN DEFAULT FALSE,
                    user_response TEXT,
                    resolved_at TEXT
                )
            ''')
            
            # 워크플로우 로그
            conn.execute('''
                CREATE TABLE IF NOT EXISTS workflow_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    phase TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    role_id TEXT,
                    description TEXT NOT NULL,
                    metadata TEXT
                )
            ''')
            
            # 프로젝트 설정
            conn.execute('''
                CREATE TABLE IF NOT EXISTS project_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
    
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger('master_orchestrator')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # 파일 핸들러
            file_handler = logging.FileHandler(self.logs_dir / 'master.log')
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)
            
            # 콘솔 핸들러
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter('%(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
        
        return logger
    
    def _define_roles(self) -> Dict[str, Dict[str, Any]]:
        """사용 가능한 역할들 정의"""
        return {
            "project_manager": {
                "name": "Project Manager",
                "description": "프로젝트 전체 관리 및 조율",
                "tools": ["communication", "timeline", "dashboard"],
                "decision_authority": "medium",
                "can_trigger_rollback": True
            },
            "business_analyst": {
                "name": "Business Analyst", 
                "description": "비즈니스 요구사항 분석",
                "tools": ["document_tracking", "modular_docs", "context_system"],
                "decision_authority": "medium",
                "can_trigger_rollback": True
            },
            "system_architect": {
                "name": "System Architect",
                "description": "시스템 아키텍처 설계",
                "tools": ["file_discovery", "ai_templates", "review_system"],
                "decision_authority": "high",
                "can_trigger_rollback": True
            },
            "frontend_developer": {
                "name": "Frontend Developer",
                "description": "프론트엔드 개발",
                "tools": ["modular_docs", "file_discovery", "communication"],
                "decision_authority": "low",
                "can_trigger_rollback": False
            },
            "backend_developer": {
                "name": "Backend Developer", 
                "description": "백엔드 개발",
                "tools": ["modular_docs", "file_discovery", "communication"],
                "decision_authority": "low",
                "can_trigger_rollback": False
            },
            "qa_tester": {
                "name": "QA Tester",
                "description": "품질 보증 및 테스트",
                "tools": ["review_system", "ai_templates", "communication"],
                "decision_authority": "medium",
                "can_trigger_rollback": True
            },
            "devops_engineer": {
                "name": "DevOps Engineer",
                "description": "배포 및 운영 환경 관리", 
                "tools": ["file_discovery", "communication", "context_system"],
                "decision_authority": "medium",
                "can_trigger_rollback": False
            }
        }
    
    def _define_workflow(self) -> List[WorkflowStep]:
        """워크플로우 단계 정의"""
        return [
            WorkflowStep(
                step_id="WF001",
                phase=ProjectPhase.PLANNING,
                roles_required=["project_manager"],
                dependencies=[],
                can_rollback_to=[],
                auto_transition=True,
                approval_required=False,
                estimated_duration="1-2시간",
                success_criteria=["프로젝트 목표 설정", "초기 계획 수립"]
            ),
            WorkflowStep(
                step_id="WF002", 
                phase=ProjectPhase.REQUIREMENTS,
                roles_required=["business_analyst"],
                dependencies=["WF001"],
                can_rollback_to=["WF001"],
                auto_transition=False,
                approval_required=True,
                estimated_duration="반나절",
                success_criteria=["요구사항 문서 완성", "이해관계자 승인"]
            ),
            WorkflowStep(
                step_id="WF003",
                phase=ProjectPhase.DESIGN,
                roles_required=["system_architect"],
                dependencies=["WF002"],
                can_rollback_to=["WF001", "WF002"],
                auto_transition=False,
                approval_required=True,
                estimated_duration="1일",
                success_criteria=["아키텍처 설계 완료", "기술 스택 결정"]
            ),
            WorkflowStep(
                step_id="WF004",
                phase=ProjectPhase.DEVELOPMENT,
                roles_required=["frontend_developer", "backend_developer"],
                dependencies=["WF003"],
                can_rollback_to=["WF002", "WF003"],
                auto_transition=True,
                approval_required=False,
                estimated_duration="2-3일",
                success_criteria=["모든 기능 구현", "코드 리뷰 완료"]
            ),
            WorkflowStep(
                step_id="WF005",
                phase=ProjectPhase.TESTING,
                roles_required=["qa_tester"],
                dependencies=["WF004"],
                can_rollback_to=["WF003", "WF004"],
                auto_transition=False,
                approval_required=False,
                estimated_duration="1일",
                success_criteria=["모든 테스트 통과", "품질 기준 달성"]
            ),
            WorkflowStep(
                step_id="WF006",
                phase=ProjectPhase.DEPLOYMENT,
                roles_required=["devops_engineer"],
                dependencies=["WF005"],
                can_rollback_to=["WF004", "WF005"],
                auto_transition=False,
                approval_required=True,
                estimated_duration="반나절",
                success_criteria=["성공적 배포", "운영 환경 안정"]
            )
        ]
    
    def start_project(self, project_config: Dict[str, Any]) -> str:
        """프로젝트 시작"""
        
        self.logger.info("🚀 새 프로젝트 시작")
        
        # 프로젝트 설정 저장
        self.project_config = project_config
        self._save_project_config(project_config)
        
        # 워크플로우 활성화
        self.workflow_active = True
        self.current_phase = ProjectPhase.PLANNING
        
        # 백그라운드 스레드 시작
        if not self.monitoring_thread.is_alive():
            self.monitoring_thread.start()
        if not self.communication_thread.is_alive():
            self.communication_thread.start()
        if not self.decision_thread.is_alive():
            self.decision_thread.start()
        if not self.chat_thread.is_alive():
            self.chat_thread.start()
        
        # 첫 번째 단계 시작
        self._start_workflow_step(ProjectPhase.PLANNING)
        
        # 워크플로우 로그
        self._log_workflow_event("project_start", None, "프로젝트 시작", project_config)
        
        return f"프로젝트 '{project_config.get('name', 'Unnamed')}' 시작됨"
    
    def _start_workflow_step(self, phase: ProjectPhase):
        """워크플로우 단계 시작"""
        
        step = next((s for s in self.workflow_steps if s.phase == phase), None)
        if not step:
            self.logger.error(f"워크플로우 단계를 찾을 수 없음: {phase}")
            return
        
        self.logger.info(f"📋 워크플로우 단계 시작: {phase.value}")
        self.current_phase = phase
        
        # 필요한 역할들 시작
        for role_id in step.roles_required:
            self._start_role_instance(role_id, step)
        
        # UI 업데이트
        self._emit_status_update()
        
        # 워크플로우 로그
        step_dict = asdict(step)
        # ProjectPhase enum을 문자열로 변환
        if 'phase' in step_dict and hasattr(step_dict['phase'], 'value'):
            step_dict['phase'] = step_dict['phase'].value
        self._log_workflow_event("step_start", None, f"단계 시작: {phase.value}", step_dict)
    
    def _start_role_instance(self, role_id: str, step: WorkflowStep):
        """역할 인스턴스 시작"""
        
        if role_id in self.role_instances and self.role_instances[role_id].status == RoleInstanceStatus.ACTIVE:
            self.logger.info(f"역할 {role_id}는 이미 활성화됨")
            return
        
        self.logger.info(f"👤 역할 인스턴스 시작: {role_id}")
        
        # 작업 디렉토리 설정
        work_dir = self.project_root / "roles" / role_id
        work_dir.mkdir(parents=True, exist_ok=True)
        
        # 로그 파일 설정
        log_file = self.logs_dir / f"{role_id}.log"
        
        # 역할별 프롬프트 생성
        role_prompt = self._generate_role_prompt(role_id, step)
        
        # Claude Code 인스턴스 실행
        try:
            process = self._start_claude_instance(role_id, work_dir, role_prompt)
            
            role_instance = RoleInstance(
                role_id=role_id,
                role_name=self.available_roles[role_id]["name"],
                process=process,
                status=RoleInstanceStatus.STARTING,
                current_task=f"{step.phase.value} 단계 작업",
                work_directory=str(work_dir),
                log_file=str(log_file),
                start_time=datetime.now(),
                last_activity=datetime.now(),
                performance_score=0.5,
                error_count=0
            )
            
            self.role_instances[role_id] = role_instance
            self._save_role_instance(role_instance)
            
            # 3초 후 상태를 ACTIVE로 변경 (실제로는 프로세스 상태 확인)
            threading.Timer(3.0, lambda: self._set_role_status(role_id, RoleInstanceStatus.ACTIVE)).start()
            
        except Exception as e:
            self.logger.error(f"역할 {role_id} 시작 실패: {str(e)}")
            self._handle_role_error(role_id, str(e))
    
    def _start_claude_instance(self, role_id: str, work_dir: Path, prompt: str) -> subprocess.Popen:
        """Claude Code 인스턴스 시작"""
        
        # Claude Code 실행 스크립트 생성
        script_content = f'''#!/bin/bash
cd "{work_dir}"

# 역할별 환경 설정
export ROLE_ID="{role_id}"
export PROJECT_ROOT="{self.project_root}"
export MASTER_HOST="localhost"
export MASTER_PORT="5000"

# Claude Code 실행 (예시 - 실제 환경에 맞게 수정 필요)
echo "Claude Code 역할 {role_id} 시작"
echo "작업 디렉토리: {work_dir}"
echo "프롬프트 길이: $(echo '{prompt}' | wc -c) 문자"

# 프롬프트를 파일로 저장
cat > prompt.txt << 'EOF'
{prompt}
EOF

# 실제로는 여기서 Claude Code API 호출하거나 CLI 실행
# claude-code --role="{role_id}" --prompt-file="prompt.txt" --project="{self.project_root}"

# 시뮬레이션을 위한 더미 프로세스
echo "$(date): {role_id} 시작됨"

# 상태 파일 생성
echo "ACTIVE" > "{work_dir}/status.txt"

# 시그널 핸들러 설정
trap 'echo "$(date): {role_id} 종료 신호 수신"; echo "STOPPED" > "{work_dir}/status.txt"; exit 0' SIGTERM SIGINT

# 주기적으로 상태 업데이트
while true; do
    echo "$(date): {role_id} 작업 중..."
    echo "$(date): ACTIVE" > "{work_dir}/status.txt"
    
    # 종료 신호 확인
    if [ -f "{work_dir}/stop.signal" ]; then
        echo "$(date): {role_id} 종료 신호 감지"
        echo "STOPPED" > "{work_dir}/status.txt"
        rm -f "{work_dir}/stop.signal"
        break
    fi
    
    # 백그라운드에서 sleep 실행하여 시그널 처리 가능하도록 함
    sleep 30 &
    wait $!
done

echo "$(date): {role_id} 종료"
'''
        
        script_path = work_dir / f"start_{role_id}.sh"
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            script_path.chmod(0o755)
            self.logger.info(f"스크립트 생성 완료: {script_path}")
        except Exception as e:
            self.logger.error(f"스크립트 생성 실패: {str(e)}")
            raise
        
        # 프로세스 시작
        try:
            process = subprocess.Popen(
                ['/bin/bash', str(script_path)],
                cwd=str(work_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                preexec_fn=os.setsid  # 프로세스 그룹 생성
            )
            
            # 프로세스가 즉시 종료되지 않았는지 확인 (3초 대기)
            time.sleep(3)
            if process.poll() is not None:
                stdout, stderr = process.communicate()
                self.logger.error(f"스크립트 조기 종료 - stdout: {stdout[:200]}, stderr: {stderr[:200]}")
                raise Exception(f"스크립트 실행 실패: {stderr}")
            
            self.logger.info(f"프로세스 시작 성공: PID {process.pid}")
            return process
        except Exception as e:
            self.logger.error(f"프로세스 시작 실패: {str(e)}")
            raise
    
    def _generate_role_prompt(self, role_id: str, step: WorkflowStep) -> str:
        """역할별 프롬프트 생성"""
        
        role_info = self.available_roles[role_id]
        
        # 도구 사용 가이드 생성
        tools_guide = self._generate_tools_guide(role_info["tools"])
        
        # 현재 단계 컨텍스트
        phase_context = self._get_phase_context(step.phase)
        
        prompt = f"""
# {role_info['name']} 역할 수행

## 현재 상황
- 프로젝트: {self.project_config.get('name', 'Unknown')}
- 현재 단계: {step.phase.value}
- 작업 목표: {step.success_criteria}

## 역할 설명
{role_info['description']}

## 현재 단계 컨텍스트
{phase_context}

## 사용 가능한 도구들
{tools_guide}

## 소통 방법
- 다른 역할과 소통이 필요하면 communication 시스템 사용
- 중요한 결정은 사용자 승인 요청
- 이전 단계로 되돌리기가 필요하면 rollback 요청

## 성공 기준
{chr(10).join(f'- {criteria}' for criteria in step.success_criteria)}

## 주의사항
- 단계별로 충분한 품질 검증 필요
- 불확실한 부분은 즉시 소통
- 작업 진행 상황을 실시간 보고

이제 작업을 시작하세요.
"""
        return prompt
    
    def _generate_tools_guide(self, available_tools: List[str]) -> str:
        """도구 사용 가이드 생성"""
        
        tools_info = {
            "communication": "다른 역할과 실시간 소통 (ActiveCommunicationEngine 사용)",
            "document_tracking": "문서 읽기/사용 추적 (DocumentTrackingSystem 사용)",
            "modular_docs": "모듈화된 문서 생성 (ModularDocumentSystem 사용)",
            "ai_templates": "AI 최적화 산출물 생성 (AIOptimizedDeliverableSystem 사용)",
            "file_discovery": "지능적 파일 탐색 (SmartFileDiscoverySystem 사용)",
            "review_system": "품질 리뷰 시스템 (IntelligentReviewEngine 사용)",
            "context_system": "컨텍스트 저장/조회 (ContextPersistenceSystem 사용)",
            "timeline": "타임라인 관리 (SimplifiedTimelineSystem 사용)",
            "dashboard": "대시보드 모니터링 (ProjectDashboardSystem 사용)"
        }
        
        guide = "### 언제 어떤 도구를 사용할지:\n"
        for tool in available_tools:
            if tool in tools_info:
                guide += f"- **{tool}**: {tools_info[tool]}\n"
        
        guide += "\n### 도구 사용 예시:\n"
        if "communication" in available_tools:
            guide += "```python\n# 다른 역할에게 질문\nfrom enhanced_communication_system import ActiveCommunicationEngine\ncomm = ActiveCommunicationEngine(project_root)\nresponse = comm.send_smart_message('backend_developer', 'API 스펙 확인 요청', MessageType.INFORMATION_REQUEST)\n```\n"
        
        return guide
    
    def _get_phase_context(self, phase: ProjectPhase) -> str:
        """단계별 컨텍스트 정보"""
        
        context_map = {
            ProjectPhase.PLANNING: "프로젝트 목표 설정, 초기 계획 수립, 리소스 계획",
            ProjectPhase.REQUIREMENTS: "비즈니스 요구사항 분석, 기능 명세, 제약사항 정의", 
            ProjectPhase.DESIGN: "시스템 아키텍처 설계, 기술 스택 선정, UI/UX 설계",
            ProjectPhase.DEVELOPMENT: "기능 구현, 코드 작성, 단위 테스트",
            ProjectPhase.TESTING: "통합 테스트, 품질 검증, 버그 수정",
            ProjectPhase.DEPLOYMENT: "배포 환경 준비, 실제 배포, 운영 준비"
        }
        
        return context_map.get(phase, "알 수 없는 단계")
    
    def request_user_decision(self, 
                            requesting_role: str,
                            title: str,
                            description: str,
                            options: List[Dict[str, Any]],
                            level: DecisionLevel = DecisionLevel.APPROVAL,
                            context: Dict[str, Any] = None,
                            deadline_hours: int = 24) -> str:
        """사용자 결정 요청"""
        
        decision_id = str(uuid.uuid4())
        deadline = datetime.now() + timedelta(hours=deadline_hours)
        
        decision = UserDecision(
            decision_id=decision_id,
            level=level,
            title=title,
            description=description,
            options=options,
            requesting_role=requesting_role,
            context=context or {},
            created_at=datetime.now(),
            deadline=deadline,
            resolved=False,
            user_response=None
        )
        
        self.pending_decisions[decision_id] = decision
        self._save_user_decision(decision)
        
        # UI로 알림 전송
        self.socketio.emit('user_decision_required', {
            'decision_id': decision_id,
            'title': title,
            'description': description,
            'options': options,
            'level': level.value,
            'deadline': deadline.isoformat()
        })
        
        self.logger.info(f"📝 사용자 결정 요청: {title} (ID: {decision_id})")
        
        return decision_id
    
    def handle_role_communication(self, from_role: str, to_role: str, message: str, message_type: str):
        """역할 간 소통 처리"""
        
        self.logger.info(f"💬 역할 소통: {from_role} → {to_role}: {message}")
        
        # 소통 기록 저장
        communication = RoleCommunication(
            communication_id=str(uuid.uuid4()),
            from_role=from_role,
            to_role=to_role,
            message=message,
            message_type=message_type,
            timestamp=datetime.now()
        )
        self.role_communications.append(communication)
        
        # 대상 역할이 활성화되어 있는지 확인
        if to_role not in self.role_instances:
            # 필요하면 역할 시작
            current_step = next((s for s in self.workflow_steps if s.phase == self.current_phase), None)
            if current_step and to_role in current_step.roles_required:
                self._start_role_instance(to_role, current_step)
        
        # 메시지 전달 (실제로는 Claude Code 인스턴스에 전달)
        self._deliver_message_to_role(to_role, from_role, message, message_type)
        
        # UI 업데이트
        self.socketio.emit('role_communication', {
            'from_role': from_role,
            'to_role': to_role,
            'message': message,
            'timestamp': communication.timestamp.isoformat()
        })
    
    def request_rollback(self, requesting_role: str, target_phase: ProjectPhase, reason: str) -> bool:
        """이전 단계로 되돌리기 요청"""
        
        self.logger.warning(f"🔄 롤백 요청: {requesting_role} → {target_phase.value}")
        
        # 롤백 권한 확인
        role_info = self.available_roles.get(requesting_role, {})
        if not role_info.get("can_trigger_rollback", False):
            self.logger.error(f"역할 {requesting_role}는 롤백 권한이 없음")
            return False
        
        # 현재 단계에서 롤백 가능한지 확인
        current_step = next((s for s in self.workflow_steps if s.phase == self.current_phase), None)
        if not current_step or target_phase.value not in [p for p in current_step.can_rollback_to]:
            self.logger.error(f"현재 단계에서 {target_phase.value}로 롤백 불가")
            return False
        
        # 사용자 승인 요청
        decision_id = self.request_user_decision(
            requesting_role=requesting_role,
            title=f"롤백 승인 요청",
            description=f"{requesting_role}가 {target_phase.value} 단계로 되돌리기를 요청했습니다.\n\n사유: {reason}",
            options=[
                {"id": "approve", "label": "승인", "description": "롤백을 승인합니다"},
                {"id": "reject", "label": "거부", "description": "롤백을 거부합니다"},
                {"id": "alternative", "label": "대안 제시", "description": "다른 해결 방안을 제시합니다"}
            ],
            level=DecisionLevel.CRITICAL,
            context={"rollback_target": target_phase.value, "reason": reason}
        )
        
        # 워크플로우 로그
        self._log_workflow_event("rollback_request", requesting_role, f"롤백 요청: {target_phase.value}", {"reason": reason})
        
        return True
    
    def _execute_rollback(self, target_phase: ProjectPhase):
        """롤백 실행"""
        
        self.logger.info(f"🔄 롤백 실행: {self.current_phase.value} → {target_phase.value}")
        
        # 현재 활성 역할들 중지
        for role_id, instance in self.role_instances.items():
            if instance.status == RoleInstanceStatus.ACTIVE:
                self._stop_role_instance(role_id)
        
        # 단계 변경
        self.current_phase = target_phase
        
        # 새 단계 시작
        self._start_workflow_step(target_phase)
        
        # 워크플로우 로그
        self._log_workflow_event("rollback_executed", None, f"롤백 완료: {target_phase.value}", {})
    
    def _stop_role_instance(self, role_id: str):
        """역할 인스턴스 중지"""
        
        if role_id not in self.role_instances:
            return
        
        instance = self.role_instances[role_id]
        self.logger.info(f"⏹️ 역할 인스턴스 중지: {role_id}")
        
        # 프로세스 종료
        if instance.process and instance.process.poll() is None:
            try:
                instance.process.terminate()
                instance.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                instance.process.kill()
                instance.process.wait()
        
        # 상태 업데이트
        instance.status = RoleInstanceStatus.STOPPED
        instance.current_task = None
        self._save_role_instance(instance)
        
        # UI 업데이트
        self._emit_status_update()
    
    def _monitoring_loop(self):
        """모니터링 루프"""
        
        while self.orchestration_active:
            try:
                # 역할 인스턴스 상태 확인
                self._check_role_instances()
                
                # 워크플로우 진행 상황 확인
                self._check_workflow_progress()
                
                # 파일 시스템 스캔
                self._perform_file_scan()
                
                # UI 데이터 업데이트
                self._emit_status_update()
                
                time.sleep(10)  # 10초마다 모니터링
                
            except Exception as e:
                self.logger.error(f"모니터링 오류: {str(e)}")
                time.sleep(30)
    
    def _communication_loop(self):
        """소통 처리 루프"""
        
        while self.orchestration_active:
            try:
                # 메시지 큐 처리
                while not self.message_queue.empty():
                    message = self.message_queue.get()
                    self._process_message(message)
                
                time.sleep(2)
                
            except Exception as e:
                self.logger.error(f"소통 처리 오류: {str(e)}")
                time.sleep(10)
    
    def _decision_loop(self):
        """사용자 결정 처리 루프"""
        
        while self.orchestration_active:
            try:
                # 결정 타임아웃 확인
                current_time = datetime.now()
                for decision_id, decision in list(self.pending_decisions.items()):
                    if not decision.resolved and decision.deadline and current_time > decision.deadline:
                        self._handle_decision_timeout(decision)
                
                time.sleep(30)  # 30초마다 확인
                
            except Exception as e:
                self.logger.error(f"결정 처리 오류: {str(e)}")
                time.sleep(60)
    
    def _setup_web_routes(self):
        """웹 라우트 설정"""
        
        @self.app.route('/')
        def dashboard():
            return render_template('dashboard.html')
        
        @self.app.route('/api/status')
        def get_status():
            return jsonify(self._get_system_status())
        
        @self.app.route('/api/roles')
        def get_roles():
            roles_data = []
            for role_instance in self.role_instances.values():
                # 직렬화 가능한 필드만 수동으로 추출
                role_dict = {
                    'role_id': role_instance.role_id,
                    'role_name': role_instance.role_name,
                    'status': role_instance.status.value,
                    'current_task': role_instance.current_task,
                    'work_directory': role_instance.work_directory,
                    'log_file': role_instance.log_file,
                    'start_time': role_instance.start_time.isoformat() if role_instance.start_time else None,
                    'last_activity': role_instance.last_activity.isoformat() if role_instance.last_activity else None,
                    'performance_score': role_instance.performance_score,
                    'error_count': role_instance.error_count,
                    # 프로세스 상태 정보 추가
                    'process_pid': role_instance.process.pid if role_instance.process else None,
                    'process_running': role_instance.process.poll() is None if role_instance.process else False
                }
                roles_data.append(role_dict)
            return jsonify(roles_data)
        
        @self.app.route('/api/decisions')
        def get_decisions():
            return jsonify([asdict(d) for d in self.pending_decisions.values() if not d.resolved])
        
        @self.app.route('/api/decision/<decision_id>', methods=['POST'])
        def handle_decision(decision_id):
            response = request.get_json()
            return jsonify(self._handle_user_decision(decision_id, response))
        
        @self.app.route('/api/files')
        def get_files():
            return jsonify(self._get_project_files())
        
        # 채팅 API 엔드포인트
        @self.app.route('/api/chat/messages')
        def get_chat_messages():
            return jsonify([{
                'message_id': msg.message_id,
                'sender': msg.sender,
                'receiver': msg.receiver,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat(),
                'message_type': msg.message_type,
                'processed': msg.processed
            } for msg in self.chat_messages[-50:]])  # 최근 50개만 반환
        
        @self.app.route('/api/chat/send', methods=['POST'])
        def send_chat_message():
            data = request.get_json()
            message = ChatMessage(
                message_id=str(uuid.uuid4()),
                sender='user',
                receiver=data.get('receiver', 'project_manager'),
                content=data.get('content', ''),
                timestamp=datetime.now(),
                message_type=data.get('message_type', 'text'),
                processed=False
            )
            self.chat_messages.append(message)
            self.message_queue.put(message)
            return jsonify({'status': 'sent', 'message_id': message.message_id})
        
        @self.app.route('/api/chat/approvals')
        def get_approval_requests():
            return jsonify([{
                'request_id': req.request_id,
                'role_id': req.role_id,
                'command': req.command,
                'description': req.description,
                'tool_name': req.tool_name,
                'parameters': req.parameters,
                'timestamp': req.timestamp.isoformat(),
                'approved': req.approved,
                'user_response': req.user_response
            } for req in self.command_approval_requests.values() if req.approved is None])
        
        @self.app.route('/api/chat/approve/<request_id>', methods=['POST'])
        def approve_command(request_id):
            data = request.get_json()
            if request_id in self.command_approval_requests:
                req = self.command_approval_requests[request_id]
                req.approved = data.get('approved', False)
                req.user_response = data.get('response', '')
                return jsonify({'status': 'processed'})
            return jsonify({'error': 'Request not found'}), 404
        
        @self.app.route('/api/role-communications')
        def get_role_communications():
            """역할 간 소통 이력 조회"""
            return jsonify([{
                'communication_id': comm.communication_id,
                'from_role': comm.from_role,
                'to_role': comm.to_role,
                'message': comm.message,
                'message_type': comm.message_type,
                'timestamp': comm.timestamp.isoformat(),
                'processed': comm.processed
            } for comm in self.role_communications[-100:]])  # 최근 100개만 반환
        
        @self.app.route('/api/files/<path:file_path>')
        def get_file_content(file_path):
            return send_file(self.project_root / file_path)
        
        @self.app.route('/api/control/start_role', methods=['POST'])
        def start_role():
            data = request.get_json()
            role_id = data.get('role_id')
            current_step = next((s for s in self.workflow_steps if s.phase == self.current_phase), None)
            if current_step:
                self._start_role_instance(role_id, current_step)
                return jsonify({"status": "success"})
            return jsonify({"status": "error", "message": "현재 단계를 찾을 수 없음"})
        
        @self.app.route('/api/control/stop_role', methods=['POST'])
        def stop_role():
            data = request.get_json()
            role_id = data.get('role_id')
            self._stop_role_instance(role_id)
            return jsonify({"status": "success"})
        
        @self.socketio.on('connect')
        def handle_connect():
            emit('connected', {'status': 'success'})
            self._emit_status_update()
    
    def _create_ui_templates(self):
        """UI 템플릿 생성"""
        
        # templates 디렉토리 생성
        templates_dir = self.master_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        # static 디렉토리 생성  
        static_dir = self.master_dir / "static"
        static_dir.mkdir(exist_ok=True)
        
        # 템플릿 파일 시스템 사용 - 하드코딩된 HTML 제거
        # dashboard.html 파일이 존재하지 않으면 기본 템플릿만 생성
        dashboard_file = templates_dir / 'dashboard.html'
        if not dashboard_file.exists():
            self.logger.info("기본 대시보드 템플릿 생성")
            # 기본 템플릿만 생성하고, 이후에는 파일 시스템의 템플릿을 사용
            pass
    
    def start_web_interface(self, host: str = '0.0.0.0', port: int = 5000):
        """웹 인터페이스 시작"""
        
        self.logger.info(f"🌐 웹 인터페이스 시작: http://{host}:{port}")
        self.socketio.run(self.app, host=host, port=port, debug=False)
    
    # Helper methods (나머지 메소드들...)
    def _set_role_status(self, role_id: str, status: RoleInstanceStatus):
        """역할 상태 설정"""
        if role_id in self.role_instances:
            self.role_instances[role_id].status = status
            self._save_role_instance(self.role_instances[role_id])
            self._emit_status_update()
    
    def _handle_role_error(self, role_id: str, error_message: str):
        """역할 오류 처리"""
        self.logger.error(f"역할 {role_id} 오류: {error_message}")
        if role_id in self.role_instances:
            self.role_instances[role_id].status = RoleInstanceStatus.ERROR
            self.role_instances[role_id].error_count += 1
    
    def _save_project_config(self, config: Dict[str, Any]):
        """프로젝트 설정 저장"""
        with sqlite3.connect(self.db_path) as conn:
            for key, value in config.items():
                conn.execute('''
                    INSERT OR REPLACE INTO project_config (key, value, updated_at)
                    VALUES (?, ?, ?)
                ''', (key, json.dumps(value), datetime.now().isoformat()))
    
    def _save_role_instance(self, instance: RoleInstance):
        """역할 인스턴스 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO role_instances
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                instance.role_id, instance.role_name, instance.status.value,
                instance.current_task, instance.work_directory, instance.log_file,
                instance.start_time.isoformat() if instance.start_time else None,
                instance.last_activity.isoformat() if instance.last_activity else None,
                instance.performance_score, instance.error_count,
                datetime.now().isoformat()
            ))
    
    def _save_user_decision(self, decision: UserDecision):
        """사용자 결정 저장"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO user_decisions
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                decision.decision_id, decision.level.value, decision.title,
                decision.description, json.dumps(decision.options),
                decision.requesting_role, json.dumps(decision.context),
                decision.created_at.isoformat(),
                decision.deadline.isoformat() if decision.deadline else None,
                decision.resolved,
                json.dumps(decision.user_response) if decision.user_response else None,
                None
            ))
    
    def _log_workflow_event(self, event_type: str, role_id: Optional[str], description: str, metadata: Any = None):
        """워크플로우 이벤트 로그"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO workflow_log (timestamp, phase, event_type, role_id, description, metadata)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(), self.current_phase.value, event_type,
                role_id, description, json.dumps(metadata) if metadata else None
            ))
    
    def _get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        active_roles = len([r for r in self.role_instances.values() if r.status == RoleInstanceStatus.ACTIVE])
        pending_decisions = len([d for d in self.pending_decisions.values() if not d.resolved])
        
        return {
            'current_phase': self.current_phase.value,
            'active_roles': active_roles,
            'pending_decisions': pending_decisions,
            'progress': self._calculate_progress(),
            'workflow_active': self.workflow_active
        }
    
    def _calculate_progress(self) -> int:
        """진행률 계산"""
        phase_weights = {
            ProjectPhase.PLANNING: 10,
            ProjectPhase.REQUIREMENTS: 20,
            ProjectPhase.DESIGN: 35,
            ProjectPhase.DEVELOPMENT: 60,
            ProjectPhase.TESTING: 85,
            ProjectPhase.DEPLOYMENT: 100
        }
        return phase_weights.get(self.current_phase, 0)
    
    def _emit_status_update(self):
        """상태 업데이트 전송"""
        status = self._get_system_status()
        self.socketio.emit('status_update', status)
    
    def _check_role_instances(self):
        """역할 인스턴스 상태 확인"""
        for role_id, instance in self.role_instances.items():
            if instance.process and instance.process.poll() is not None:
                # 프로세스가 종료됨
                if instance.status != RoleInstanceStatus.STOPPED:
                    self.logger.warning(f"역할 {role_id} 프로세스가 예상치 못하게 종료됨")
                    instance.status = RoleInstanceStatus.ERROR
                    instance.error_count += 1
                    self._save_role_instance(instance)
                    
                    # 에러 카운트가 3번 미만이면 재시작 시도
                    if instance.error_count < 3:
                        self.logger.info(f"역할 {role_id} 재시작 시도 ({instance.error_count}/3)")
                        self._restart_role_instance(role_id)
                    else:
                        self.logger.error(f"역할 {role_id} 재시작 시도 초과, 중단됨")
            
            # 상태 파일 확인
            elif instance.status == RoleInstanceStatus.ACTIVE:
                status_file = Path(instance.work_directory) / "status.txt"
                if status_file.exists():
                    try:
                        with open(status_file, 'r') as f:
                            status_content = f.read().strip()
                        if "ACTIVE" in status_content:
                            instance.last_activity = datetime.now()
                            self._save_role_instance(instance)
                    except Exception as e:
                        self.logger.error(f"상태 파일 읽기 실패: {str(e)}")
    
    def _restart_role_instance(self, role_id: str):
        """역할 인스턴스 재시작"""
        if role_id not in self.role_instances:
            return
        
        instance = self.role_instances[role_id]
        
        # 이전 프로세스 정리
        if instance.process and instance.process.poll() is None:
            instance.process.terminate()
            instance.process.wait(timeout=5)
        
        # 새로운 프로세스 시작
        try:
            current_step = next((s for s in self.workflow_steps if s.phase == self.current_phase), None)
            if current_step:
                role_prompt = self._generate_role_prompt(role_id, current_step)
                work_dir = Path(instance.work_directory)
                new_process = self._start_claude_instance(role_id, work_dir, role_prompt)
                
                instance.process = new_process
                instance.status = RoleInstanceStatus.STARTING
                instance.last_activity = datetime.now()
                self._save_role_instance(instance)
                
                # 3초 후 상태를 ACTIVE로 변경
                threading.Timer(3.0, lambda: self._set_role_status(role_id, RoleInstanceStatus.ACTIVE)).start()
                
        except Exception as e:
            self.logger.error(f"역할 {role_id} 재시작 실패: {str(e)}")
            instance.status = RoleInstanceStatus.ERROR
            self._save_role_instance(instance)
    
    def _check_workflow_progress(self):
        """워크플로우 진행 상황 확인"""
        # 현재 단계의 모든 역할이 완료되었는지 확인
        current_step = next((s for s in self.workflow_steps if s.phase == self.current_phase), None)
        if not current_step:
            return
        
        # 모든 필수 역할이 작업을 완료했는지 확인하는 로직 필요
        # 실제로는 각 역할의 산출물을 확인하거나 완료 신호를 받아야 함
        pass
    
    def _perform_file_scan(self):
        """파일 시스템 스캔"""
        try:
            self.file_discovery.scan_project_files()
        except Exception as e:
            self.logger.error(f"파일 스캔 오류: {str(e)}")
    
    def _get_project_files(self) -> List[Dict[str, Any]]:
        """프로젝트 파일 목록 조회"""
        try:
            search_results = self.file_discovery.smart_search(SearchQuery(limit=100))
            return [asdict(result) for result in search_results]
        except Exception as e:
            self.logger.error(f"파일 목록 조회 오류: {str(e)}")
            return []
    
    def _handle_user_decision(self, decision_id: str, response: Dict[str, Any]) -> Dict[str, Any]:
        """사용자 결정 처리"""
        if decision_id not in self.pending_decisions:
            return {"status": "error", "message": "결정을 찾을 수 없음"}
        
        decision = self.pending_decisions[decision_id]
        decision.resolved = True
        decision.user_response = response
        
        self._save_user_decision(decision)
        
        # 결정에 따른 액션 수행
        self._execute_user_decision(decision)
        
        del self.pending_decisions[decision_id]
        
        return {"status": "success"}
    
    def _execute_user_decision(self, decision: UserDecision):
        """사용자 결정 실행"""
        option_id = decision.user_response.get("option_id")
        
        # 롤백 승인 처리
        if decision.context.get("rollback_target"):
            if option_id == "approve":
                target_phase = ProjectPhase(decision.context["rollback_target"])
                self._execute_rollback(target_phase)
            elif option_id == "reject":
                self.logger.info("롤백 거부됨")
            
        # 다른 결정 타입들도 여기서 처리
    
    def _deliver_message_to_role(self, to_role: str, from_role: str, message: str, message_type: str):
        """역할에게 메시지 전달"""
        # 실제로는 Claude Code 인스턴스에 메시지를 전달해야 함
        # 현재는 로그만 기록
        self.logger.info(f"메시지 전달: {from_role} → {to_role}: {message}")
    
    def _process_message(self, message: Dict[str, Any]):
        """메시지 처리"""
        # 메시지 큐에서 온 메시지들을 처리
        pass
    
    def _chat_processing_loop(self):
        """채팅 메시지 처리 루프"""
        while self.orchestration_active:
            try:
                # 메시지 큐에서 메시지 처리
                message = self.message_queue.get(timeout=1)
                self._process_chat_message(message)
                self.message_queue.task_done()
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"채팅 메시지 처리 오류: {str(e)}")
    
    def _process_chat_message(self, message: ChatMessage):
        """채팅 메시지 처리"""
        if message.sender == 'user':
            # 사용자 메시지를 역할에게 전달
            self._deliver_message_to_role(message.receiver, 'user', message.content, message.message_type)
            
            # 역할이 실제 Claude Code 인스턴스라면 응답 생성
            if message.receiver in self.role_instances:
                response = self._generate_role_response(message.receiver, message.content)
                if response:
                    # 응답 메시지 생성
                    response_message = ChatMessage(
                        message_id=str(uuid.uuid4()),
                        sender=message.receiver,
                        receiver='user',
                        content=response,
                        timestamp=datetime.now(),
                        message_type='response',
                        processed=True
                    )
                    self.chat_messages.append(response_message)
                    
                    # 웹소켓으로 실시간 알림
                    self.socketio.emit('new_message', {
                        'message_id': response_message.message_id,
                        'sender': response_message.sender,
                        'content': response_message.content,
                        'timestamp': response_message.timestamp.isoformat(),
                        'message_type': response_message.message_type
                    })
        
        message.processed = True
    
    def _generate_role_response(self, role_id: str, user_message: str) -> str:
        """실제 Claude Code 인스턴스와 통신하여 응답 생성"""
        try:
            # 역할의 작업 디렉토리 확인
            role_dir = self.project_root / "roles" / role_id
            if not role_dir.exists():
                return f"역할 {role_id}를 찾을 수 없습니다."
            
            # 메시지 파일 생성 (Claude Code 인스턴스에서 읽을 수 있도록)
            message_file = role_dir / "user_message.txt"
            with open(message_file, 'w', encoding='utf-8') as f:
                f.write(f"사용자 메시지: {user_message}\n")
                f.write(f"시간: {datetime.now().isoformat()}\n")
                f.write("이 메시지에 대해 응답해주세요.\n")
            
            # 응답 파일 경로
            response_file = role_dir / "response.txt"
            if response_file.exists():
                response_file.unlink()  # 이전 응답 삭제
            
            # Claude Code 인스턴스가 실행 중인지 확인
            role_instance = self.role_instances.get(role_id)
            if not role_instance or not role_instance.is_running():
                return f"역할 {role_id}가 현재 실행 중이지 않습니다."
            
            # 응답 대기 (최대 30초)
            max_wait = 30
            wait_count = 0
            while wait_count < max_wait:
                if response_file.exists():
                    try:
                        with open(response_file, 'r', encoding='utf-8') as f:
                            response = f.read().strip()
                        if response:
                            response_file.unlink()  # 응답 파일 삭제
                            return response
                    except:
                        pass
                time.sleep(1)
                wait_count += 1
            
            # 타임아웃 시 기본 응답
            role_name = self.available_roles.get(role_id, {}).get('name', role_id)
            return f"{role_name}입니다. 메시지를 받았지만 현재 다른 작업을 처리 중입니다. 잠시 후 다시 시도해주세요."
            
        except Exception as e:
            self.logger.error(f"역할 응답 생성 오류: {str(e)}")
            return f"죄송합니다. 응답 생성 중 오류가 발생했습니다: {str(e)}"
    
    def _request_command_approval(self, role_id: str, command: str, description: str, tool_name: str, parameters: Dict[str, Any]) -> str:
        """명령어 승인 요청"""
        request_id = str(uuid.uuid4())
        approval_request = CommandApprovalRequest(
            request_id=request_id,
            role_id=role_id,
            command=command,
            description=description,
            tool_name=tool_name,
            parameters=parameters,
            timestamp=datetime.now()
        )
        
        self.command_approval_requests[request_id] = approval_request
        
        # 웹소켓으로 승인 요청 알림
        self.socketio.emit('approval_request', {
            'request_id': request_id,
            'role_id': role_id,
            'command': command,
            'description': description,
            'tool_name': tool_name,
            'parameters': parameters
        })
        
        return request_id
    
    def _handle_decision_timeout(self, decision: UserDecision):
        """결정 타임아웃 처리"""
        self.logger.warning(f"사용자 결정 타임아웃: {decision.title}")
        
        # 기본 액션 수행 또는 에스컬레이션
        decision.resolved = True
        decision.user_response = {"option_id": "timeout", "note": "타임아웃으로 인한 자동 처리"}
        
        self._save_user_decision(decision)
        del self.pending_decisions[decision.decision_id]

def main():
    """메인 함수"""
    print("🎯 Master Orchestrator 시작...")
    
    orchestrator = MasterOrchestrator(".")
    
    # 예시 프로젝트 시작
    project_config = {
        "name": "Web Community Platform",
        "description": "사용자 간 소통을 위한 웹 커뮤니티 플랫폼",
        "features": ["사용자 인증", "게시판", "댓글 시스템", "실시간 알림"],
        "tech_stack": {"frontend": "React", "backend": "Node.js", "database": "PostgreSQL"}
    }
    
    # 프로젝트 시작
    result = orchestrator.start_project(project_config)
    print(f"✅ {result}")
    
    # 웹 인터페이스 시작
    print("🌐 웹 인터페이스를 시작합니다...")
    print("브라우저에서 http://localhost:5000 접속")
    
    try:
        orchestrator.start_web_interface(port=5000)
    except KeyboardInterrupt:
        print("\n👋 Master Orchestrator 종료")
        orchestrator.orchestration_active = False

if __name__ == "__main__":
    main()