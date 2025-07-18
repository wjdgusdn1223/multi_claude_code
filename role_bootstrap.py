#!/usr/bin/env python3
"""
Role Bootstrap System
각 역할의 Claude Code가 시작될 때 자동으로 실행되어 상황을 파악하고 규칙을 인식하는 시스템
"""

import os
import sys
import yaml
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

class RoleBootstrap:
    def __init__(self):
        self.role_dir = Path.cwd()
        self.project_root = self.role_dir.parent.parent
        self.role_id = self.role_dir.name
        self.system_initialized = False
        
        # 설정 파일들 로드
        self.load_system_configuration()
        self.load_role_configuration()
        self.load_current_status()
    
    def load_system_configuration(self):
        """시스템 전체 설정 로드"""
        try:
            # 역할 정의 로드
            with open(self.project_root / "roles.yaml", 'r', encoding='utf-8') as f:
                self.roles_config = yaml.safe_load(f)
            
            # 자동화 룰 로드
            with open(self.project_root / "automation_rules.yaml", 'r', encoding='utf-8') as f:
                self.automation_rules = yaml.safe_load(f)
            
            # 프로젝트 설정 로드
            with open(self.project_root / "project_config.yaml", 'r', encoding='utf-8') as f:
                self.project_config = yaml.safe_load(f)
            
            self.system_initialized = True
            
        except Exception as e:
            print(f"⚠️  시스템 설정 로드 실패: {str(e)}")
            self.system_initialized = False
    
    def load_role_configuration(self):
        """현재 역할 설정 로드"""
        if not self.system_initialized:
            return
        
        try:
            self.role_config = self.roles_config['roles'][self.role_id]
            self.role_name = self.role_config['role_name']
            self.responsibilities = self.role_config['responsibilities']
            self.deliverables = self.role_config['deliverables']
            self.dependencies = self.role_config.get('dependencies', [])
            self.collaborators = self.role_config.get('collaborates_with', [])
            self.reports_to = self.role_config.get('reports_to', [])
            
        except KeyError as e:
            print(f"⚠️  역할 설정 오류: {self.role_id} 역할을 찾을 수 없습니다")
            sys.exit(1)
    
    def load_current_status(self):
        """현재 상태 로드"""
        status_file = self.role_dir / "status.yaml"
        
        if status_file.exists():
            try:
                with open(status_file, 'r', encoding='utf-8') as f:
                    self.current_status = yaml.safe_load(f)
                    
                # 상태 검증
                self.validate_status_structure()
                
            except Exception as e:
                print(f"⚠️  상태 파일 로드 실패: {str(e)}")
                self.initialize_default_status()
        else:
            self.initialize_default_status()
    
    def initialize_default_status(self):
        """기본 상태 초기화"""
        self.current_status = {
            'role_info': {
                'role_name': self.role_name,
                'role_id': self.role_id,
                'assigned_to': f"claude-{self.role_id}",
                'start_date': datetime.now().isoformat(),
                'last_updated': datetime.now().isoformat()
            },
            'current_status': {
                'phase': 'planning',
                'progress_percentage': 0,
                'current_task': '초기화',
                'next_task': '의존성 확인',
                'ready_to_start': False
            },
            'dependencies': {
                'waiting_for': self.dependencies.copy(),
                'blocking': [],
                'ready_to_start': False
            },
            'tasks': {
                'pending': self.responsibilities.copy(),
                'in_progress': [],
                'completed': [],
                'blocked': []
            },
            'deliverables': {
                'required': self.deliverables.copy(),
                'in_progress': [],
                'completed': [],
                'approved': []
            },
            'inputs': {
                'required': [],
                'received': [],
                'missing': []
            },
            'outputs': {
                'produced': [],
                'delivered_to': [],
                'pending_delivery': []
            },
            'communication': {
                'last_sync': datetime.now().isoformat(),
                'pending_questions': [],
                'decisions_needed': [],
                'escalations': []
            },
            'context': {
                'project_name': self.project_config.get('project', {}).get('name', 'Unknown'),
                'project_phase': self.project_config.get('phases', {}).get('current', 'unknown'),
                'team_size': len(self.roles_config['roles']),
                'priority': self.project_config.get('project', {}).get('priority', 'medium')
            }
        }
        
        self.save_status()
    
    def validate_status_structure(self):
        """상태 구조 검증"""
        required_sections = [
            'role_info', 'current_status', 'dependencies', 'tasks',
            'deliverables', 'inputs', 'outputs', 'communication', 'context'
        ]
        
        for section in required_sections:
            if section not in self.current_status:
                print(f"⚠️  상태 구조 오류: {section} 섹션 누락")
                self.initialize_default_status()
                return
        
        # 마지막 업데이트 시간 갱신
        self.current_status['role_info']['last_updated'] = datetime.now().isoformat()
    
    def check_dependencies(self) -> bool:
        """의존성 확인"""
        if not self.dependencies:
            self.current_status['dependencies']['ready_to_start'] = True
            return True
        
        missing_deps = []
        ready_deps = []
        
        for dep_role in self.dependencies:
            dep_status_file = self.project_root / "roles" / dep_role / "status.yaml"
            
            if not dep_status_file.exists():
                missing_deps.append(dep_role)
                continue
            
            try:
                with open(dep_status_file, 'r', encoding='utf-8') as f:
                    dep_status = yaml.safe_load(f)
                
                dep_phase = dep_status.get('current_status', {}).get('phase', 'planning')
                
                if dep_phase in ['completed', 'review']:
                    ready_deps.append(dep_role)
                else:
                    missing_deps.append(dep_role)
                    
            except Exception as e:
                print(f"⚠️  의존성 확인 오류 ({dep_role}): {str(e)}")
                missing_deps.append(dep_role)
        
        # 의존성 상태 업데이트
        self.current_status['dependencies']['waiting_for'] = missing_deps
        self.current_status['dependencies']['ready_to_start'] = len(missing_deps) == 0
        
        if missing_deps:
            self.current_status['current_status']['current_task'] = f"의존성 대기 중: {', '.join(missing_deps)}"
            print(f"⏳ 의존성 대기 중: {', '.join(missing_deps)}")
        else:
            print("✅ 모든 의존성이 충족되었습니다")
        
        return len(missing_deps) == 0
    
    def check_inputs(self) -> List[str]:
        """필요한 입력 확인"""
        available_inputs = []
        
        # 공유 디렉토리에서 입력 확인
        shared_dir = self.project_root / "shared"
        if shared_dir.exists():
            for input_file in shared_dir.rglob("*"):
                if input_file.is_file():
                    available_inputs.append(str(input_file.relative_to(shared_dir)))
        
        # 의존성 역할들의 산출물 확인
        for dep_role in self.dependencies:
            dep_deliverables_dir = self.project_root / "roles" / dep_role / "deliverables"
            if dep_deliverables_dir.exists():
                for deliverable in dep_deliverables_dir.rglob("*"):
                    if deliverable.is_file():
                        available_inputs.append(f"{dep_role}:{deliverable.name}")
        
        return available_inputs
    
    def check_communications(self) -> List[Dict]:
        """통신 메시지 확인"""
        messages = []
        comm_dir = self.project_root / "communication" / f"to_{self.role_id}"
        
        if comm_dir.exists():
            for msg_file in comm_dir.glob("*.yaml"):
                try:
                    with open(msg_file, 'r', encoding='utf-8') as f:
                        message = yaml.safe_load(f)
                    
                    messages.append({
                        'file': msg_file.name,
                        'from': message.get('from_role', 'unknown'),
                        'type': message.get('type', 'unknown'),
                        'timestamp': message.get('timestamp', 'unknown'),
                        'content': message.get('content', {})
                    })
                    
                except Exception as e:
                    print(f"⚠️  메시지 로드 오류 ({msg_file}): {str(e)}")
        
        return messages
    
    def send_message(self, to_role: str, msg_type: str, content: Dict, priority: str = "medium"):
        """다른 역할에게 메시지 전송"""
        comm_dir = self.project_root / "communication" / f"from_{self.role_id}"
        comm_dir.mkdir(parents=True, exist_ok=True)
        
        message = {
            'from_role': self.role_id,
            'to_role': to_role,
            'type': msg_type,
            'priority': priority,
            'timestamp': datetime.now().isoformat(),
            'content': content
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        msg_file = comm_dir / f"{timestamp}_{msg_type}_{to_role}.yaml"
        
        with open(msg_file, 'w', encoding='utf-8') as f:
            yaml.dump(message, f, default_flow_style=False)
        
        print(f"📨 메시지 전송: {to_role} <- {msg_type}")
    
    def report_to_master(self, report_type: str, content: Dict):
        """마스터에게 보고"""
        self.send_message("master", report_type, content, "high")
    
    def update_status(self, **kwargs):
        """상태 업데이트"""
        for key, value in kwargs.items():
            if '.' in key:
                # 중첩된 키 처리 (예: "current_status.progress_percentage")
                parts = key.split('.')
                current = self.current_status
                
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                current[parts[-1]] = value
            else:
                self.current_status[key] = value
        
        # 마지막 업데이트 시간 갱신
        self.current_status['role_info']['last_updated'] = datetime.now().isoformat()
        
        # 상태 저장
        self.save_status()
    
    def save_status(self):
        """상태 저장"""
        status_file = self.role_dir / "status.yaml"
        
        try:
            with open(status_file, 'w', encoding='utf-8') as f:
                yaml.dump(self.current_status, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            print(f"⚠️  상태 저장 실패: {str(e)}")
    
    def get_next_task(self) -> Optional[str]:
        """다음 작업 결정"""
        pending_tasks = self.current_status['tasks']['pending']
        
        if not pending_tasks:
            return None
        
        # 의존성이 충족되지 않은 경우
        if not self.current_status['dependencies']['ready_to_start']:
            return "의존성 대기"
        
        # 첫 번째 대기 중인 작업 반환
        return pending_tasks[0]
    
    def start_task(self, task_name: str):
        """작업 시작"""
        pending = self.current_status['tasks']['pending']
        in_progress = self.current_status['tasks']['in_progress']
        
        if task_name in pending:
            pending.remove(task_name)
            in_progress.append(task_name)
            
            self.update_status(**{
                'current_status.current_task': task_name,
                'current_status.phase': 'in_progress'
            })
            
            print(f"🚀 작업 시작: {task_name}")
    
    def complete_task(self, task_name: str):
        """작업 완료"""
        in_progress = self.current_status['tasks']['in_progress']
        completed = self.current_status['tasks']['completed']
        
        if task_name in in_progress:
            in_progress.remove(task_name)
            completed.append(task_name)
            
            # 진행률 계산
            total_tasks = len(self.responsibilities)
            completed_tasks = len(completed)
            progress = int((completed_tasks / total_tasks) * 100)
            
            self.update_status(**{
                'current_status.progress_percentage': progress
            })
            
            print(f"✅ 작업 완료: {task_name} ({progress}%)")
            
            # 마스터에게 보고
            self.report_to_master("task_completed", {
                'task_name': task_name,
                'progress': progress,
                'completed_tasks': completed_tasks,
                'total_tasks': total_tasks
            })
    
    def generate_startup_report(self) -> str:
        """시작 시 상황 보고서 생성"""
        deps_status = "✅ 준비됨" if self.current_status['dependencies']['ready_to_start'] else "⏳ 대기 중"
        
        report = f"""
# {self.role_name} 시작 보고서

## 기본 정보
- 역할: {self.role_name} ({self.role_id})
- 프로젝트: {self.current_status['context']['project_name']}
- 현재 단계: {self.current_status['context']['project_phase']}

## 현재 상태
- 단계: {self.current_status['current_status']['phase']}
- 진행률: {self.current_status['current_status']['progress_percentage']}%
- 현재 작업: {self.current_status['current_status']['current_task']}

## 의존성
- 상태: {deps_status}
- 대기 중: {', '.join(self.current_status['dependencies']['waiting_for']) if self.current_status['dependencies']['waiting_for'] else '없음'}

## 할당된 책임
{chr(10).join(f"- {resp}" for resp in self.responsibilities)}

## 필수 산출물
{chr(10).join(f"- {deliv}" for deliv in self.deliverables)}

## 협업 대상
{', '.join(self.collaborators) if self.collaborators else '없음'}

## 다음 작업
{self.get_next_task() or '모든 작업 완료'}
"""
        return report
    
    def create_claude_instructions(self) -> str:
        """Claude Code에 대한 지시사항 생성"""
        instructions = f"""
# {self.role_name} 역할 지시사항

당신은 멀티 Claude Code 시스템의 **{self.role_name}** 역할을 담당합니다.

## 🎯 현재 상황
{self.generate_startup_report()}

## 📋 작업 순서
1. **상태 확인**: `cat status.yaml`로 현재 상태 파악
2. **의존성 체크**: 필요한 입력물들이 준비되었는지 확인
3. **통신 확인**: `ls ../communication/to_{self.role_id}/` 메시지 확인
4. **작업 수행**: 할당된 책임사항 수행
5. **상태 업데이트**: 진행상황을 status.yaml에 실시간 기록
6. **산출물 생성**: deliverables/ 디렉토리에 결과물 저장
7. **협업**: 다른 역할들과 소통

## 🔄 자동화 규칙
- 작업 완료 시 자동으로 status.yaml 업데이트
- 중요한 진행사항은 마스터에게 보고
- 블로커 발생 시 즉시 에스컬레이션
- 의존성 문제는 자동으로 해당 역할에게 알림

## 📨 통신 방법
- 메시지 수신: `../communication/to_{self.role_id}/`
- 메시지 발송: `../communication/from_{self.role_id}/`
- 마스터 보고: `../communication/to_master/`

## 🚨 중요사항
- 모든 변경사항은 즉시 status.yaml에 반영
- 다른 역할의 의존성을 고려하여 신속하게 작업
- 품질 기준을 준수하여 산출물 생성
- 문제 발생 시 즉시 보고 및 에스컬레이션

## 💡 유용한 명령어
```bash
# 현재 상태 확인
cat status.yaml

# 통신 메시지 확인
ls -la ../communication/to_{self.role_id}/

# 의존성 상태 확인
cat ../roles/{{dependency_role}}/status.yaml

# 산출물 디렉토리 확인
ls -la deliverables/

# 마스터에게 보고
python3 ../../role_bootstrap.py --report "보고내용"
```

지금 시작하세요! 🚀
"""
        return instructions
    
    def initialize_role_environment(self):
        """역할 환경 초기화"""
        # 필수 디렉토리 생성
        (self.role_dir / "deliverables").mkdir(exist_ok=True)
        (self.role_dir / "working").mkdir(exist_ok=True)
        (self.role_dir / "docs").mkdir(exist_ok=True)
        
        # 통신 디렉토리 생성
        comm_base = self.project_root / "communication"
        (comm_base / f"to_{self.role_id}").mkdir(parents=True, exist_ok=True)
        (comm_base / f"from_{self.role_id}").mkdir(parents=True, exist_ok=True)
        
        # 지시사항 파일 생성
        instructions_file = self.role_dir / "CLAUDE_INSTRUCTIONS.md"
        with open(instructions_file, 'w', encoding='utf-8') as f:
            f.write(self.create_claude_instructions())
        
        print("🏗️  역할 환경 초기화 완료")
    
    def run_startup_sequence(self):
        """시작 시퀀스 실행"""
        print(f"🚀 {self.role_name} 초기화 시작")
        
        # 1. 환경 초기화
        self.initialize_role_environment()
        
        # 2. 의존성 확인
        dependencies_ready = self.check_dependencies()
        
        # 3. 통신 확인
        messages = self.check_communications()
        if messages:
            print(f"📨 {len(messages)}개의 메시지 수신")
        
        # 4. 입력 확인
        inputs = self.check_inputs()
        if inputs:
            print(f"📁 {len(inputs)}개의 입력 발견")
        
        # 5. 다음 작업 결정
        next_task = self.get_next_task()
        if next_task:
            print(f"📋 다음 작업: {next_task}")
        
        # 6. 상태 업데이트
        self.update_status(**{
            'current_status.next_task': next_task or '없음',
            'inputs.received': inputs,
            'communication.last_sync': datetime.now().isoformat()
        })
        
        # 7. 마스터에게 시작 보고
        self.report_to_master("role_started", {
            'role_name': self.role_name,
            'dependencies_ready': dependencies_ready,
            'messages_count': len(messages),
            'inputs_count': len(inputs),
            'next_task': next_task
        })
        
        print(f"✅ {self.role_name} 초기화 완료")
        print(f"📄 지시사항: cat CLAUDE_INSTRUCTIONS.md")


def main():
    """메인 함수"""
    bootstrap = RoleBootstrap()
    
    if not bootstrap.system_initialized:
        print("❌ 시스템 초기화 실패")
        sys.exit(1)
    
    bootstrap.run_startup_sequence()


if __name__ == "__main__":
    main()