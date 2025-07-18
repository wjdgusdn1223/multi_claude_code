#!/usr/bin/env python3
"""
Multi-Claude Code Master Controller
마스터 역할을 하는 Claude Code가 다른 역할들을 제어하는 시스템
"""

import os
import yaml
import json
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class Phase(Enum):
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    REVIEW = "review"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    PAUSED = "paused"

class Priority(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

@dataclass
class RoleStatus:
    role_id: str
    role_name: str
    phase: Phase
    progress: int
    dependencies: List[str]
    ready_to_start: bool
    current_task: str
    last_updated: datetime
    pid: Optional[int] = None  # Claude Code process ID

class MasterController:
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.roles_config = self.load_roles_config()
        self.automation_rules = self.load_automation_rules()
        self.active_roles: Dict[str, RoleStatus] = {}
        self.communication_queue = []
        self.project_history = []
        self.checkpoint_data = {}
        
        # 통신 디렉토리 설정
        self.communication_dir = self.project_root / "communication"
        self.communication_dir.mkdir(exist_ok=True)
        
        # 마스터 로그 설정
        self.log_file = self.project_root / "master_log.txt"
        
        # 백그라운드 모니터링 시작
        self.monitoring_thread = threading.Thread(target=self.monitor_roles, daemon=True)
        self.monitoring_thread.start()
    
    def load_roles_config(self) -> Dict[str, Any]:
        """roles.yaml 파일 로드"""
        roles_file = self.project_root / "roles.yaml"
        if not roles_file.exists():
            raise FileNotFoundError("roles.yaml not found")
        
        with open(roles_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def load_automation_rules(self) -> Dict[str, Any]:
        """automation_rules.yaml 파일 로드"""
        rules_file = self.project_root / "automation_rules.yaml"
        if not rules_file.exists():
            raise FileNotFoundError("automation_rules.yaml not found")
        
        with open(rules_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def log_action(self, action: str, details: str = ""):
        """마스터 액션 로그"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {action}: {details}\n"
        
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        print(f"🎯 Master: {action} - {details}")
    
    def create_role_instructions(self, role_id: str) -> str:
        """각 역할에 대한 자동 지시사항 생성"""
        role_config = self.roles_config['roles'][role_id]
        
        instructions = f"""
# {role_config['role_name']} 역할 지시사항

## 시스템 개요
당신은 멀티 Claude Code 시스템의 {role_config['role_name']} 역할입니다.
현재 디렉토리: roles/{role_id}/

## 필수 작업 순서
1. 현재 상태 파악: status.yaml 파일 읽기
2. 의존성 체크: 필요한 입력물들이 준비되었는지 확인
3. 작업 수행: 할당된 책임사항 수행
4. 상태 업데이트: 진행상황을 status.yaml에 기록
5. 산출물 생성: 요구되는 deliverables 생성
6. 통신: 다른 역할들과의 협업 메시지 처리

## 주요 책임사항
{chr(10).join(f"- {resp}" for resp in role_config['responsibilities'])}

## 필수 산출물
{chr(10).join(f"- {deliv}" for deliv in role_config['deliverables'])}

## 의존성 관리
- 의존대상: {role_config.get('dependencies', [])}
- 협업대상: {role_config.get('collaborates_with', [])}
- 보고대상: {role_config.get('reports_to', [])}

## 통신 프로토콜
1. 다른 역할로부터 메시지 수신: ../communication/to_{role_id}/ 디렉토리 확인
2. 다른 역할에게 메시지 전송: ../communication/from_{role_id}/ 디렉토리에 파일 생성
3. 마스터에게 보고: ../communication/to_master/ 디렉토리에 보고서 생성

## 자동화 규칙
- 상태 업데이트 주기: 5분마다 또는 작업 완료시
- 의존성 체크: 작업 시작 전 필수
- 품질 게이트: 단계 완료 시 자동 체크
- 에스컬레이션: 24시간 이상 블로킹 시 자동 보고

## 중요 사항
- 항상 status.yaml을 최신 상태로 유지
- 모든 산출물은 타임스탬프와 함께 저장
- 다른 역할과의 협업을 위해 정기적으로 통신 디렉토리 확인
- 문제 발생시 즉시 마스터에게 보고
- 작업 완료 시 반드시 다음 역할에게 통지

## 현재 프로젝트 컨텍스트
{self.get_current_project_context()}
"""
        return instructions
    
    def get_current_project_context(self) -> str:
        """현재 프로젝트 상황 요약"""
        try:
            with open(self.project_root / "project_config.yaml", 'r') as f:
                config = yaml.safe_load(f)
            
            return f"""
프로젝트명: {config.get('project', {}).get('name', 'Unknown')}
현재 단계: {config.get('phases', {}).get('current', 'unknown')}
활성 역할 수: {len(self.active_roles)}
전체 진행률: {self.calculate_overall_progress()}%
"""
        except:
            return "프로젝트 정보를 불러올 수 없습니다."
    
    def calculate_overall_progress(self) -> int:
        """전체 프로젝트 진행률 계산"""
        if not self.active_roles:
            return 0
        
        total_progress = sum(role.progress for role in self.active_roles.values())
        return total_progress // len(self.active_roles)
    
    def start_role(self, role_id: str, force: bool = False) -> bool:
        """특정 역할의 Claude Code 시작"""
        if role_id not in self.roles_config['roles']:
            self.log_action("ERROR", f"Unknown role: {role_id}")
            return False
        
        role_dir = self.project_root / "roles" / role_id
        
        # 의존성 체크
        if not force and not self.check_dependencies(role_id):
            self.log_action("DEPENDENCY_NOT_MET", f"Role {role_id} dependencies not satisfied")
            return False
        
        # 역할 지시사항 생성
        instructions = self.create_role_instructions(role_id)
        instructions_file = role_dir / "ROLE_INSTRUCTIONS.md"
        
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(instructions)
        
        # Claude Code 실행
        try:
            cmd = ["claude-code", "--resume"]
            process = subprocess.Popen(
                cmd,
                cwd=str(role_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # 역할 상태 추가
            self.active_roles[role_id] = RoleStatus(
                role_id=role_id,
                role_name=self.roles_config['roles'][role_id]['role_name'],
                phase=Phase.IN_PROGRESS,
                progress=0,
                dependencies=self.roles_config['roles'][role_id].get('dependencies', []),
                ready_to_start=True,
                current_task="초기화 중",
                last_updated=datetime.now(),
                pid=process.pid
            )
            
            self.log_action("ROLE_STARTED", f"Started {role_id} with PID {process.pid}")
            return True
            
        except Exception as e:
            self.log_action("ERROR", f"Failed to start {role_id}: {str(e)}")
            return False
    
    def check_dependencies(self, role_id: str) -> bool:
        """역할의 의존성 체크"""
        role_config = self.roles_config['roles'][role_id]
        dependencies = role_config.get('dependencies', [])
        
        for dep_role_id in dependencies:
            dep_status_file = self.project_root / "roles" / dep_role_id / "status.yaml"
            
            if not dep_status_file.exists():
                return False
            
            try:
                with open(dep_status_file, 'r', encoding='utf-8') as f:
                    dep_status = yaml.safe_load(f)
                
                if dep_status['current_status']['phase'] not in ['completed', 'review']:
                    return False
                    
            except Exception:
                return False
        
        return True
    
    def monitor_roles(self):
        """백그라운드에서 역할들 모니터링"""
        while True:
            try:
                self.check_communications()
                self.update_role_statuses()
                self.handle_automatic_transitions()
                time.sleep(30)  # 30초마다 체크
            except Exception as e:
                self.log_action("MONITOR_ERROR", str(e))
    
    def check_communications(self):
        """역할간 통신 메시지 처리"""
        comm_dir = self.project_root / "communication"
        
        # 마스터에게 온 메시지 처리
        to_master_dir = comm_dir / "to_master"
        if to_master_dir.exists():
            for msg_file in to_master_dir.glob("*.yaml"):
                self.process_master_message(msg_file)
        
        # 역할간 메시지 라우팅
        self.route_inter_role_messages()
    
    def process_master_message(self, msg_file: Path):
        """마스터에게 온 메시지 처리"""
        try:
            with open(msg_file, 'r', encoding='utf-8') as f:
                message = yaml.safe_load(f)
            
            sender = message.get('from_role')
            msg_type = message.get('type')
            content = message.get('content')
            
            self.log_action("MESSAGE_RECEIVED", f"From {sender}: {msg_type}")
            
            if msg_type == "status_update":
                self.handle_status_update(sender, content)
            elif msg_type == "deliverable_ready":
                self.handle_deliverable_ready(sender, content)
            elif msg_type == "blocker_report":
                self.handle_blocker_report(sender, content)
            elif msg_type == "help_request":
                self.handle_help_request(sender, content)
            
            # 처리된 메시지 아카이브
            archive_dir = self.project_root / "communication" / "archive"
            archive_dir.mkdir(exist_ok=True)
            msg_file.rename(archive_dir / f"{datetime.now().isoformat()}_{msg_file.name}")
            
        except Exception as e:
            self.log_action("MESSAGE_ERROR", f"Failed to process {msg_file}: {str(e)}")
    
    def route_inter_role_messages(self):
        """역할간 메시지 라우팅"""
        comm_dir = self.project_root / "communication"
        
        for from_dir in comm_dir.glob("from_*"):
            sender_role = from_dir.name[5:]  # "from_" 제거
            
            for msg_file in from_dir.glob("*.yaml"):
                try:
                    with open(msg_file, 'r', encoding='utf-8') as f:
                        message = yaml.safe_load(f)
                    
                    target_role = message.get('to_role')
                    if target_role:
                        target_dir = comm_dir / f"to_{target_role}"
                        target_dir.mkdir(exist_ok=True)
                        
                        # 메시지 복사
                        target_file = target_dir / f"{sender_role}_{msg_file.name}"
                        with open(target_file, 'w', encoding='utf-8') as f:
                            yaml.dump(message, f, default_flow_style=False)
                        
                        self.log_action("MESSAGE_ROUTED", f"{sender_role} -> {target_role}")
                        
                        # 원본 메시지 아카이브
                        archive_dir = comm_dir / "archive"
                        archive_dir.mkdir(exist_ok=True)
                        msg_file.rename(archive_dir / f"{datetime.now().isoformat()}_{msg_file.name}")
                        
                except Exception as e:
                    self.log_action("ROUTING_ERROR", f"Failed to route {msg_file}: {str(e)}")
    
    def handle_status_update(self, role_id: str, content: Dict):
        """역할 상태 업데이트 처리"""
        if role_id in self.active_roles:
            self.active_roles[role_id].progress = content.get('progress', 0)
            self.active_roles[role_id].current_task = content.get('current_task', '')
            self.active_roles[role_id].last_updated = datetime.now()
    
    def handle_deliverable_ready(self, role_id: str, content: Dict):
        """산출물 준비 완료 처리"""
        deliverable = content.get('deliverable_name')
        self.log_action("DELIVERABLE_READY", f"{role_id}: {deliverable}")
        
        # 의존하는 역할들에게 알림
        self.notify_dependent_roles(role_id, deliverable)
    
    def notify_dependent_roles(self, completed_role: str, deliverable: str):
        """의존하는 역할들에게 알림"""
        for role_id, role_config in self.roles_config['roles'].items():
            if completed_role in role_config.get('dependencies', []):
                # 자동으로 역할 시작
                if role_id not in self.active_roles:
                    self.start_role(role_id)
    
    def handle_blocker_report(self, role_id: str, content: Dict):
        """블로커 보고 처리"""
        blocker = content.get('blocker_description')
        self.log_action("BLOCKER_REPORTED", f"{role_id}: {blocker}")
        
        # 자동 해결 시도
        self.attempt_blocker_resolution(role_id, content)
    
    def attempt_blocker_resolution(self, role_id: str, blocker_info: Dict):
        """블로커 자동 해결 시도"""
        blocker_type = blocker_info.get('type')
        
        if blocker_type == "missing_dependency":
            # 의존성 역할 시작
            missing_role = blocker_info.get('missing_role')
            if missing_role:
                self.start_role(missing_role, force=True)
        
        elif blocker_type == "resource_unavailable":
            # 리소스 할당 시도
            self.allocate_resources(role_id, blocker_info)
    
    def rollback_to_phase(self, target_phase: str):
        """특정 단계로 롤백"""
        self.log_action("ROLLBACK_INITIATED", f"Rolling back to {target_phase}")
        
        # 현재 단계 이후 역할들 중단
        phases_order = ["planning", "execution", "monitoring", "closure"]
        target_index = phases_order.index(target_phase)
        
        for role_id in list(self.active_roles.keys()):
            role_phase = self.get_role_phase_index(role_id)
            if role_phase > target_index:
                self.stop_role(role_id)
        
        # 체크포인트 복원
        self.restore_checkpoint(target_phase)
    
    def stop_role(self, role_id: str):
        """역할 중단"""
        if role_id in self.active_roles:
            role_status = self.active_roles[role_id]
            if role_status.pid:
                try:
                    os.kill(role_status.pid, 9)  # SIGKILL
                    self.log_action("ROLE_STOPPED", f"Stopped {role_id}")
                except:
                    pass
            
            del self.active_roles[role_id]
    
    def create_checkpoint(self, phase: str):
        """체크포인트 생성"""
        checkpoint_dir = self.project_root / "checkpoints" / phase
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        # 현재 상태 저장
        checkpoint_data = {
            'timestamp': datetime.now().isoformat(),
            'phase': phase,
            'active_roles': {role_id: {
                'progress': role.progress,
                'current_task': role.current_task,
                'phase': role.phase.value
            } for role_id, role in self.active_roles.items()},
            'project_state': self.get_project_state()
        }
        
        with open(checkpoint_dir / "checkpoint.yaml", 'w', encoding='utf-8') as f:
            yaml.dump(checkpoint_data, f, default_flow_style=False)
        
        self.log_action("CHECKPOINT_CREATED", f"Created checkpoint for {phase}")
    
    def restore_checkpoint(self, phase: str):
        """체크포인트 복원"""
        checkpoint_file = self.project_root / "checkpoints" / phase / "checkpoint.yaml"
        
        if not checkpoint_file.exists():
            self.log_action("CHECKPOINT_NOT_FOUND", f"No checkpoint for {phase}")
            return False
        
        try:
            with open(checkpoint_file, 'r', encoding='utf-8') as f:
                checkpoint_data = yaml.safe_load(f)
            
            # 상태 복원
            self.restore_project_state(checkpoint_data['project_state'])
            
            self.log_action("CHECKPOINT_RESTORED", f"Restored checkpoint for {phase}")
            return True
            
        except Exception as e:
            self.log_action("CHECKPOINT_ERROR", f"Failed to restore {phase}: {str(e)}")
            return False
    
    def get_project_state(self) -> Dict:
        """현재 프로젝트 상태 수집"""
        # 모든 역할의 상태 파일 수집
        state = {}
        for role_id in self.roles_config['roles']:
            status_file = self.project_root / "roles" / role_id / "status.yaml"
            if status_file.exists():
                with open(status_file, 'r', encoding='utf-8') as f:
                    state[role_id] = yaml.safe_load(f)
        
        return state
    
    def restore_project_state(self, state: Dict):
        """프로젝트 상태 복원"""
        for role_id, role_state in state.items():
            status_file = self.project_root / "roles" / role_id / "status.yaml"
            with open(status_file, 'w', encoding='utf-8') as f:
                yaml.dump(role_state, f, default_flow_style=False)
    
    def get_system_status(self) -> Dict:
        """전체 시스템 상태 조회"""
        return {
            'active_roles': len(self.active_roles),
            'overall_progress': self.calculate_overall_progress(),
            'roles_status': {role_id: {
                'phase': role.phase.value,
                'progress': role.progress,
                'current_task': role.current_task,
                'last_updated': role.last_updated.isoformat()
            } for role_id, role in self.active_roles.items()},
            'communication_queue_size': len(self.communication_queue)
        }


def main():
    """마스터 컨트롤러 메인 함수"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Multi-Claude Code Master Controller')
    parser.add_argument('--start-role', help='Start a specific role')
    parser.add_argument('--stop-role', help='Stop a specific role')
    parser.add_argument('--rollback', help='Rollback to a specific phase')
    parser.add_argument('--status', action='store_true', help='Show system status')
    parser.add_argument('--checkpoint', help='Create checkpoint for a phase')
    
    args = parser.parse_args()
    
    controller = MasterController()
    
    if args.start_role:
        controller.start_role(args.start_role)
    elif args.stop_role:
        controller.stop_role(args.stop_role)
    elif args.rollback:
        controller.rollback_to_phase(args.rollback)
    elif args.status:
        status = controller.get_system_status()
        print(json.dumps(status, indent=2))
    elif args.checkpoint:
        controller.create_checkpoint(args.checkpoint)
    else:
        print("Multi-Claude Code Master Controller")
        print("Use --help for available commands")


if __name__ == "__main__":
    main()