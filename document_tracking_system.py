#!/usr/bin/env python3
"""
Document Tracking System for Multi-Agent Claude Code
산출물 읽기/사용 추적 및 지능적 문서 관리 시스템
"""

import os
import json
import yaml
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum

class DocumentType(Enum):
    REQUIREMENT = "requirement"
    SPECIFICATION = "specification"
    DESIGN = "design"
    CODE = "code"
    TEST = "test"
    REPORT = "report"
    PLAN = "plan"
    REVIEW = "review"

class AccessType(Enum):
    READ = "read"
    REFERENCED = "referenced"
    MODIFIED = "modified"
    VALIDATED = "validated"
    APPROVED = "approved"
    REJECTED = "rejected"

@dataclass
class DocumentMetadata:
    """문서 메타데이터"""
    file_path: str
    document_type: DocumentType
    role_owner: str
    title: str
    description: str
    created_at: datetime
    last_modified: datetime
    version: str
    dependencies: List[str]
    dependents: List[str]
    tags: List[str]
    purpose: str
    target_readers: List[str]
    content_hash: str
    size_bytes: int
    
@dataclass
class DocumentAccess:
    """문서 접근 기록"""
    access_id: str
    document_path: str
    role_id: str
    access_type: AccessType
    timestamp: datetime
    duration_seconds: Optional[int]
    content_read_percentage: Optional[float]
    purpose: str
    notes: str
    context: Dict[str, Any]

@dataclass
class DocumentUsage:
    """문서 사용 분석"""
    document_path: str
    total_accesses: int
    unique_readers: Set[str]
    last_accessed: datetime
    average_read_time: float
    content_utilization: float
    feedback_count: int
    issues_raised: int
    approval_status: str

class DocumentTrackingSystem:
    """문서 추적 시스템"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.tracking_dir = self.project_root / "tracking"
        self.tracking_dir.mkdir(exist_ok=True)
        
        self.metadata_file = self.tracking_dir / "document_metadata.json"
        self.access_log_file = self.tracking_dir / "document_access_log.json"
        self.usage_stats_file = self.tracking_dir / "document_usage_stats.json"
        
        self.metadata_registry = self._load_metadata_registry()
        self.access_logs = self._load_access_logs()
        self.usage_stats = self._load_usage_stats()
    
    def register_document(self, 
                         file_path: str, 
                         role_owner: str, 
                         document_type: DocumentType,
                         metadata: Dict[str, Any]) -> bool:
        """문서 등록"""
        try:
            full_path = self.project_root / file_path
            
            if not full_path.exists():
                print(f"문서가 존재하지 않습니다: {file_path}")
                return False
            
            # 파일 내용 해시 계산
            content_hash = self._calculate_file_hash(full_path)
            file_size = full_path.stat().st_size
            
            doc_metadata = DocumentMetadata(
                file_path=file_path,
                document_type=document_type,
                role_owner=role_owner,
                title=metadata.get('title', full_path.name),
                description=metadata.get('description', ''),
                created_at=datetime.now(),
                last_modified=datetime.fromtimestamp(full_path.stat().st_mtime),
                version=metadata.get('version', '1.0'),
                dependencies=metadata.get('dependencies', []),
                dependents=metadata.get('dependents', []),
                tags=metadata.get('tags', []),
                purpose=metadata.get('purpose', ''),
                target_readers=metadata.get('target_readers', []),
                content_hash=content_hash,
                size_bytes=file_size
            )
            
            self.metadata_registry[file_path] = asdict(doc_metadata)
            self._save_metadata_registry()
            
            print(f"✅ 문서 등록 완료: {file_path}")
            return True
            
        except Exception as e:
            print(f"❌ 문서 등록 실패: {str(e)}")
            return False
    
    def log_document_access(self,
                           document_path: str,
                           role_id: str,
                           access_type: AccessType,
                           purpose: str = "",
                           duration_seconds: Optional[int] = None,
                           content_read_percentage: Optional[float] = None,
                           notes: str = "",
                           context: Dict[str, Any] = None) -> str:
        """문서 접근 로깅"""
        access_id = f"{role_id}_{document_path.replace('/', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        access_record = DocumentAccess(
            access_id=access_id,
            document_path=document_path,
            role_id=role_id,
            access_type=access_type,
            timestamp=datetime.now(),
            duration_seconds=duration_seconds,
            content_read_percentage=content_read_percentage,
            purpose=purpose,
            notes=notes,
            context=context or {}
        )
        
        # 접근 로그 저장
        access_key = f"{datetime.now().isoformat()}_{access_id}"
        self.access_logs[access_key] = asdict(access_record)
        self._save_access_logs()
        
        # 사용 통계 업데이트
        self._update_usage_stats(access_record)
        
        print(f"📖 문서 접근 기록: {role_id} -> {document_path} ({access_type.value})")
        return access_id
    
    def get_document_metadata(self, document_path: str) -> Optional[DocumentMetadata]:
        """문서 메타데이터 조회"""
        metadata_dict = self.metadata_registry.get(document_path)
        if metadata_dict:
            # datetime 객체 복원
            metadata_dict['created_at'] = datetime.fromisoformat(metadata_dict['created_at'])
            metadata_dict['last_modified'] = datetime.fromisoformat(metadata_dict['last_modified'])
            metadata_dict['document_type'] = DocumentType(metadata_dict['document_type'])
            return DocumentMetadata(**metadata_dict)
        return None
    
    def get_documents_for_role(self, role_id: str, include_recommendations: bool = True) -> List[Dict[str, Any]]:
        """역할별 필요 문서 목록"""
        relevant_docs = []
        
        for doc_path, metadata in self.metadata_registry.items():
            doc_metadata = self.get_document_metadata(doc_path)
            if not doc_metadata:
                continue
            
            # 직접적으로 지정된 독자인지 확인
            is_target_reader = role_id in doc_metadata.target_readers
            
            # 의존성 기반 추천
            is_dependency = self._is_dependency_for_role(role_id, doc_path)
            
            # 관련도 점수 계산
            relevance_score = self._calculate_relevance_score(role_id, doc_metadata)
            
            if is_target_reader or is_dependency or (include_recommendations and relevance_score > 0.5):
                doc_info = {
                    'path': doc_path,
                    'metadata': asdict(doc_metadata),
                    'is_target_reader': is_target_reader,
                    'is_dependency': is_dependency,
                    'relevance_score': relevance_score,
                    'read_status': self._get_read_status(role_id, doc_path),
                    'last_accessed': self._get_last_access_time(role_id, doc_path),
                    'priority': self._calculate_document_priority(role_id, doc_metadata)
                }
                relevant_docs.append(doc_info)
        
        # 우선순위 순으로 정렬
        relevant_docs.sort(key=lambda x: (x['priority'], -x['relevance_score']), reverse=True)
        
        return relevant_docs
    
    def get_unread_critical_documents(self, role_id: str) -> List[Dict[str, Any]]:
        """읽지 않은 중요 문서 목록"""
        unread_critical = []
        
        for doc_path, metadata in self.metadata_registry.items():
            doc_metadata = self.get_document_metadata(doc_path)
            if not doc_metadata:
                continue
            
            # 중요도 평가
            is_critical = self._is_critical_for_role(role_id, doc_metadata)
            is_read = self._has_role_read_document(role_id, doc_path)
            
            if is_critical and not is_read:
                doc_info = {
                    'path': doc_path,
                    'title': doc_metadata.title,
                    'owner': doc_metadata.role_owner,
                    'urgency': self._calculate_urgency(doc_metadata),
                    'blocking_factor': self._calculate_blocking_factor(role_id, doc_path),
                    'estimated_read_time': self._estimate_read_time(doc_metadata),
                    'summary': doc_metadata.description
                }
                unread_critical.append(doc_info)
        
        # 긴급도 순으로 정렬
        unread_critical.sort(key=lambda x: (x['urgency'], x['blocking_factor']), reverse=True)
        
        return unread_critical
    
    def track_document_usage_in_task(self, role_id: str, task_name: str, documents_used: List[str]) -> Dict[str, Any]:
        """작업 중 문서 사용 추적"""
        usage_record = {
            'role_id': role_id,
            'task_name': task_name,
            'timestamp': datetime.now().isoformat(),
            'documents_used': documents_used,
            'usage_analysis': {}
        }
        
        for doc_path in documents_used:
            # 문서 사용 기록
            access_id = self.log_document_access(
                document_path=doc_path,
                role_id=role_id,
                access_type=AccessType.REFERENCED,
                purpose=f"Task: {task_name}에서 참조",
                context={'task': task_name, 'usage_type': 'task_execution'}
            )
            
            # 사용 분석
            doc_metadata = self.get_document_metadata(doc_path)
            if doc_metadata:
                usage_record['usage_analysis'][doc_path] = {
                    'access_id': access_id,
                    'document_type': doc_metadata.document_type.value,
                    'owner': doc_metadata.role_owner,
                    'relevance_to_task': self._assess_document_relevance_to_task(doc_path, task_name),
                    'usage_effectiveness': self._assess_usage_effectiveness(role_id, doc_path, task_name)
                }
        
        # 작업-문서 사용 기록 저장
        usage_file = self.tracking_dir / f"task_document_usage_{role_id}.json"
        
        existing_usage = {}
        if usage_file.exists():
            with open(usage_file, 'r', encoding='utf-8') as f:
                existing_usage = json.load(f)
        
        existing_usage[f"{task_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"] = usage_record
        
        with open(usage_file, 'w', encoding='utf-8') as f:
            json.dump(existing_usage, f, indent=2, ensure_ascii=False, default=str)
        
        return usage_record
    
    def generate_document_recommendations(self, role_id: str, current_task: str = "") -> List[Dict[str, Any]]:
        """문서 추천"""
        recommendations = []
        
        # 현재 작업과 관련된 문서 추천
        if current_task:
            task_related_docs = self._find_task_related_documents(role_id, current_task)
            recommendations.extend(task_related_docs)
        
        # 역할 기반 필수 문서 추천
        role_essential_docs = self._find_role_essential_documents(role_id)
        recommendations.extend(role_essential_docs)
        
        # 협업 기반 추천
        collaborative_docs = self._find_collaborative_documents(role_id)
        recommendations.extend(collaborative_docs)
        
        # 중복 제거 및 우선순위 정렬
        unique_recommendations = self._deduplicate_recommendations(recommendations)
        unique_recommendations.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return unique_recommendations[:10]  # 상위 10개 추천
    
    def create_reading_schedule(self, role_id: str) -> Dict[str, Any]:
        """읽기 일정 생성"""
        unread_docs = self.get_unread_critical_documents(role_id)
        recommended_docs = self.generate_document_recommendations(role_id)
        
        schedule = {
            'role_id': role_id,
            'created_at': datetime.now().isoformat(),
            'immediate_priority': [],  # 즉시 읽어야 할 문서
            'today_schedule': [],      # 오늘 읽을 문서
            'this_week': [],           # 이번 주 읽을 문서
            'optional_reading': []     # 선택적 읽기
        }
        
        # 긴급도에 따른 분류
        for doc in unread_docs:
            if doc['urgency'] >= 0.9:
                schedule['immediate_priority'].append(doc)
            elif doc['urgency'] >= 0.7:
                schedule['today_schedule'].append(doc)
            elif doc['urgency'] >= 0.5:
                schedule['this_week'].append(doc)
            else:
                schedule['optional_reading'].append(doc)
        
        # 추천 문서 추가
        for rec_doc in recommended_docs:
            if rec_doc['recommendation_score'] >= 0.8:
                schedule['today_schedule'].append(rec_doc)
            elif rec_doc['recommendation_score'] >= 0.6:
                schedule['this_week'].append(rec_doc)
            else:
                schedule['optional_reading'].append(rec_doc)
        
        # 읽기 시간 추정
        schedule['estimated_time'] = {
            'immediate': sum(doc.get('estimated_read_time', 15) for doc in schedule['immediate_priority']),
            'today': sum(doc.get('estimated_read_time', 15) for doc in schedule['today_schedule']),
            'this_week': sum(doc.get('estimated_read_time', 15) for doc in schedule['this_week'])
        }
        
        return schedule
    
    def update_role_status_with_tracking(self, role_id: str, status_updates: Dict[str, Any]) -> Dict[str, Any]:
        """역할 상태에 문서 추적 정보 통합"""
        # 기존 상태 로드
        status_file = self.project_root / "roles" / role_id / "status.yaml"
        current_status = {}
        
        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                current_status = yaml.safe_load(f)
        
        # 문서 추적 정보 추가
        document_tracking = {
            'documents_accessed_today': self._get_todays_accesses(role_id),
            'unread_critical_count': len(self.get_unread_critical_documents(role_id)),
            'reading_schedule': self.create_reading_schedule(role_id),
            'document_usage_efficiency': self._calculate_usage_efficiency(role_id),
            'knowledge_gaps': self._identify_knowledge_gaps(role_id),
            'last_tracking_update': datetime.now().isoformat()
        }
        
        # 상태 업데이트
        current_status.update(status_updates)
        current_status['document_tracking'] = document_tracking
        
        # 상태 저장
        with open(status_file, 'w', encoding='utf-8') as f:
            yaml.dump(current_status, f, default_flow_style=False, allow_unicode=True)
        
        return current_status
    
    # Helper methods
    def _load_metadata_registry(self) -> Dict[str, Any]:
        """메타데이터 레지스트리 로드"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_metadata_registry(self):
        """메타데이터 레지스트리 저장"""
        with open(self.metadata_file, 'w', encoding='utf-8') as f:
            json.dump(self.metadata_registry, f, indent=2, ensure_ascii=False, default=str)
    
    def _load_access_logs(self) -> Dict[str, Any]:
        """접근 로그 로드"""
        if self.access_log_file.exists():
            try:
                with open(self.access_log_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_access_logs(self):
        """접근 로그 저장"""
        with open(self.access_log_file, 'w', encoding='utf-8') as f:
            json.dump(self.access_logs, f, indent=2, ensure_ascii=False, default=str)
    
    def _load_usage_stats(self) -> Dict[str, Any]:
        """사용 통계 로드"""
        if self.usage_stats_file.exists():
            try:
                with open(self.usage_stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_usage_stats(self):
        """사용 통계 저장"""
        with open(self.usage_stats_file, 'w', encoding='utf-8') as f:
            json.dump(self.usage_stats, f, indent=2, ensure_ascii=False, default=str)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
        except Exception:
            return ""
        return hash_md5.hexdigest()
    
    def _update_usage_stats(self, access_record: DocumentAccess):
        """사용 통계 업데이트"""
        doc_path = access_record.document_path
        
        if doc_path not in self.usage_stats:
            self.usage_stats[doc_path] = {
                'total_accesses': 0,
                'unique_readers': set(),
                'last_accessed': None,
                'read_times': [],
                'feedback_count': 0,
                'issues_raised': 0,
                'approval_status': 'pending'
            }
        
        stats = self.usage_stats[doc_path]
        stats['total_accesses'] += 1
        stats['unique_readers'].add(access_record.role_id)
        stats['last_accessed'] = access_record.timestamp.isoformat()
        
        if access_record.duration_seconds:
            stats['read_times'].append(access_record.duration_seconds)
        
        # Set을 list로 변환하여 JSON 직렬화 가능하게 함
        stats['unique_readers'] = list(stats['unique_readers'])
        
        self._save_usage_stats()
    
    def _is_dependency_for_role(self, role_id: str, doc_path: str) -> bool:
        """역할에 대한 의존성 문서인지 확인"""
        # 역할 간 의존성 매핑을 기반으로 판단
        role_dependencies = {
            'requirements_analyst': ['business_requirements.md', 'functional_specifications.md'],
            'system_architect': ['technical_requirements.md', 'business_requirements.md'],
            'frontend_developer': ['ui_designs.md', 'system_architecture.md']
        }
        
        required_docs = role_dependencies.get(role_id, [])
        return any(req_doc in doc_path for req_doc in required_docs)
    
    def _calculate_relevance_score(self, role_id: str, doc_metadata: DocumentMetadata) -> float:
        """관련도 점수 계산"""
        score = 0.0
        
        # 타겟 독자인 경우
        if role_id in doc_metadata.target_readers:
            score += 0.8
        
        # 문서 타입 기반 관련도
        role_doc_relevance = {
            'business_analyst': [DocumentType.REQUIREMENT, DocumentType.SPECIFICATION],
            'system_architect': [DocumentType.DESIGN, DocumentType.SPECIFICATION],
            'frontend_developer': [DocumentType.DESIGN, DocumentType.CODE]
        }
        
        if role_id in role_doc_relevance:
            if doc_metadata.document_type in role_doc_relevance[role_id]:
                score += 0.5
        
        # 태그 기반 관련도
        role_tags = {
            'frontend_developer': ['ui', 'frontend', 'react', 'javascript'],
            'backend_developer': ['api', 'backend', 'nodejs', 'database'],
            'system_architect': ['architecture', 'system', 'design', 'technical']
        }
        
        if role_id in role_tags:
            matching_tags = set(doc_metadata.tags) & set(role_tags[role_id])
            score += len(matching_tags) * 0.1
        
        return min(score, 1.0)
    
    def _get_read_status(self, role_id: str, doc_path: str) -> Dict[str, Any]:
        """읽기 상태 조회"""
        accesses = [
            access for access in self.access_logs.values()
            if access['role_id'] == role_id and access['document_path'] == doc_path
        ]
        
        if not accesses:
            return {'status': 'unread', 'last_access': None, 'read_count': 0}
        
        latest_access = max(accesses, key=lambda x: x['timestamp'])
        
        return {
            'status': 'read',
            'last_access': latest_access['timestamp'],
            'read_count': len(accesses),
            'total_read_time': sum(a.get('duration_seconds', 0) for a in accesses),
            'average_completion': sum(a.get('content_read_percentage', 0) for a in accesses) / len(accesses)
        }
    
    def _get_last_access_time(self, role_id: str, doc_path: str) -> Optional[str]:
        """마지막 접근 시간 조회"""
        accesses = [
            access for access in self.access_logs.values()
            if access['role_id'] == role_id and access['document_path'] == doc_path
        ]
        
        if accesses:
            latest = max(accesses, key=lambda x: x['timestamp'])
            return latest['timestamp']
        return None
    
    def _calculate_document_priority(self, role_id: str, doc_metadata: DocumentMetadata) -> float:
        """문서 우선순위 계산"""
        priority = 0.0
        
        # 타겟 독자 우선순위
        if role_id in doc_metadata.target_readers:
            priority += 0.8
        
        # 문서 타입별 우선순위
        type_priority = {
            DocumentType.REQUIREMENT: 0.9,
            DocumentType.SPECIFICATION: 0.8,
            DocumentType.DESIGN: 0.7,
            DocumentType.PLAN: 0.6,
            DocumentType.REPORT: 0.4
        }
        priority += type_priority.get(doc_metadata.document_type, 0.3)
        
        # 최신성 고려
        days_old = (datetime.now() - doc_metadata.last_modified).days
        freshness_factor = max(0, 1.0 - (days_old / 30))  # 30일이 지나면 0
        priority += freshness_factor * 0.2
        
        return min(priority, 1.0)
    
    def _is_critical_for_role(self, role_id: str, doc_metadata: DocumentMetadata) -> bool:
        """역할에 대한 중요 문서인지 판단"""
        # 직접 타겟 독자인 경우
        if role_id in doc_metadata.target_readers:
            return True
        
        # 의존성 문서인 경우
        if self._is_dependency_for_role(role_id, doc_metadata.file_path):
            return True
        
        # 관련도 점수가 높은 경우
        relevance = self._calculate_relevance_score(role_id, doc_metadata)
        return relevance >= 0.7
    
    def _has_role_read_document(self, role_id: str, doc_path: str) -> bool:
        """역할이 문서를 읽었는지 확인"""
        read_status = self._get_read_status(role_id, doc_path)
        return read_status['status'] == 'read'
    
    def _calculate_urgency(self, doc_metadata: DocumentMetadata) -> float:
        """긴급도 계산"""
        urgency = 0.5  # 기본값
        
        # 최신성 기반 긴급도
        hours_old = (datetime.now() - doc_metadata.last_modified).total_seconds() / 3600
        if hours_old < 2:
            urgency += 0.4
        elif hours_old < 24:
            urgency += 0.2
        
        # 문서 타입별 긴급도
        type_urgency = {
            DocumentType.REQUIREMENT: 0.9,
            DocumentType.SPECIFICATION: 0.8,
            DocumentType.DESIGN: 0.6
        }
        urgency += type_urgency.get(doc_metadata.document_type, 0.1)
        
        return min(urgency, 1.0)
    
    def _calculate_blocking_factor(self, role_id: str, doc_path: str) -> float:
        """블로킹 요소 계산"""
        # 이 문서가 역할의 작업을 얼마나 블로킹하는지 평가
        doc_metadata = self.get_document_metadata(doc_path)
        if not doc_metadata:
            return 0.0
        
        # 의존성 문서인 경우 높은 블로킹 요소
        if self._is_dependency_for_role(role_id, doc_path):
            return 0.9
        
        # 타겟 독자인 경우
        if role_id in doc_metadata.target_readers:
            return 0.7
        
        return 0.3
    
    def _estimate_read_time(self, doc_metadata: DocumentMetadata) -> int:
        """읽기 시간 추정 (분)"""
        # 파일 크기 기반 추정 (대략 1KB당 1분)
        estimated_minutes = max(5, doc_metadata.size_bytes // 1024)
        
        # 문서 타입별 조정
        type_multiplier = {
            DocumentType.REQUIREMENT: 1.5,
            DocumentType.SPECIFICATION: 1.8,
            DocumentType.DESIGN: 1.3,
            DocumentType.CODE: 2.0,
            DocumentType.REPORT: 1.0
        }
        
        multiplier = type_multiplier.get(doc_metadata.document_type, 1.0)
        return int(estimated_minutes * multiplier)
    
    def _assess_document_relevance_to_task(self, doc_path: str, task_name: str) -> float:
        """작업에 대한 문서 관련도 평가"""
        # 작업명과 문서 경로/내용의 키워드 매칭
        task_keywords = task_name.lower().split()
        doc_keywords = doc_path.lower().split('/')
        
        matches = len(set(task_keywords) & set(doc_keywords))
        return min(matches / len(task_keywords), 1.0) if task_keywords else 0.0
    
    def _assess_usage_effectiveness(self, role_id: str, doc_path: str, task_name: str) -> float:
        """사용 효과성 평가"""
        # 간단한 효과성 점수 (실제로는 더 복잡한 로직 필요)
        return 0.8  # 임시값
    
    def _find_task_related_documents(self, role_id: str, task_name: str) -> List[Dict[str, Any]]:
        """작업 관련 문서 찾기"""
        related_docs = []
        task_keywords = task_name.lower().split()
        
        for doc_path, metadata in self.metadata_registry.items():
            doc_metadata = self.get_document_metadata(doc_path)
            if not doc_metadata:
                continue
            
            # 키워드 매칭
            doc_text = f"{doc_metadata.title} {doc_metadata.description} {' '.join(doc_metadata.tags)}".lower()
            relevance = sum(1 for keyword in task_keywords if keyword in doc_text) / len(task_keywords)
            
            if relevance > 0.3:
                related_docs.append({
                    'path': doc_path,
                    'metadata': asdict(doc_metadata),
                    'recommendation_score': relevance,
                    'recommendation_reason': f"Task '{task_name}' 관련성: {relevance:.2f}"
                })
        
        return related_docs
    
    def _find_role_essential_documents(self, role_id: str) -> List[Dict[str, Any]]:
        """역할 필수 문서 찾기"""
        essential_docs = []
        
        for doc_path, metadata in self.metadata_registry.items():
            doc_metadata = self.get_document_metadata(doc_path)
            if not doc_metadata:
                continue
            
            if role_id in doc_metadata.target_readers:
                essential_docs.append({
                    'path': doc_path,
                    'metadata': asdict(doc_metadata),
                    'recommendation_score': 0.9,
                    'recommendation_reason': "역할의 필수 읽기 문서"
                })
        
        return essential_docs
    
    def _find_collaborative_documents(self, role_id: str) -> List[Dict[str, Any]]:
        """협업 관련 문서 찾기"""
        # 다른 역할들이 최근에 많이 접근한 문서들
        collaborative_docs = []
        
        # 최근 7일간의 접근 로그 분석
        recent_cutoff = datetime.now() - timedelta(days=7)
        
        doc_access_count = {}
        for access in self.access_logs.values():
            access_time = datetime.fromisoformat(access['timestamp'])
            if access_time > recent_cutoff and access['role_id'] != role_id:
                doc_path = access['document_path']
                doc_access_count[doc_path] = doc_access_count.get(doc_path, 0) + 1
        
        # 접근 빈도가 높은 문서들 추천
        for doc_path, access_count in doc_access_count.items():
            if access_count >= 3:  # 최소 3번 이상 접근된 문서
                doc_metadata = self.get_document_metadata(doc_path)
                if doc_metadata:
                    score = min(access_count / 10, 0.8)  # 최대 0.8점
                    collaborative_docs.append({
                        'path': doc_path,
                        'metadata': asdict(doc_metadata),
                        'recommendation_score': score,
                        'recommendation_reason': f"다른 역할들이 {access_count}회 접근한 문서"
                    })
        
        return collaborative_docs
    
    def _deduplicate_recommendations(self, recommendations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """추천 중복 제거"""
        seen_paths = set()
        unique_recs = []
        
        for rec in recommendations:
            path = rec['path']
            if path not in seen_paths:
                seen_paths.add(path)
                unique_recs.append(rec)
        
        return unique_recs
    
    def _get_todays_accesses(self, role_id: str) -> List[Dict[str, Any]]:
        """오늘의 접근 기록"""
        today = datetime.now().date()
        todays_accesses = []
        
        for access in self.access_logs.values():
            if (access['role_id'] == role_id and 
                datetime.fromisoformat(access['timestamp']).date() == today):
                todays_accesses.append(access)
        
        return todays_accesses
    
    def _calculate_usage_efficiency(self, role_id: str) -> float:
        """사용 효율성 계산"""
        # 간단한 효율성 지표 (실제로는 더 복잡한 계산)
        recent_accesses = self._get_todays_accesses(role_id)
        
        if not recent_accesses:
            return 0.0
        
        # 평균 읽기 완료율
        completion_rates = [
            access.get('content_read_percentage', 0) 
            for access in recent_accesses 
            if access.get('content_read_percentage') is not None
        ]
        
        if completion_rates:
            return sum(completion_rates) / len(completion_rates) / 100
        
        return 0.5  # 기본값

    def _identify_knowledge_gaps(self, role_id: str) -> List[str]:
        """지식 격차 식별"""
        gaps = []
        
        # 읽지 않은 중요 문서들
        unread_critical = self.get_unread_critical_documents(role_id)
        
        for doc in unread_critical:
            gaps.append(f"미읽음: {doc['title']}")
        
        # 낮은 이해도 문서들
        for access in self.access_logs.values():
            if (access['role_id'] == role_id and 
                access.get('content_read_percentage', 100) < 50):
                gaps.append(f"낮은 이해도: {access['document_path']}")
        
        return gaps[:5]  # 상위 5개만 반환

def main():
    """테스트 및 데모"""
    tracker = DocumentTrackingSystem("/home/jungh/workspace/web_community_project")
    
    # 예시: 문서 등록
    tracker.register_document(
        file_path="roles/business_analyst/deliverables/business_requirements.md",
        role_owner="business_analyst",
        document_type=DocumentType.REQUIREMENT,
        metadata={
            'title': 'Web Community Platform Business Requirements',
            'description': '웹 커뮤니티 플랫폼의 비즈니스 요구사항',
            'target_readers': ['requirements_analyst', 'system_architect', 'product_owner'],
            'tags': ['requirements', 'business', 'community', 'web'],
            'purpose': '프로젝트의 비즈니스 요구사항 정의 및 공유'
        }
    )
    
    # 예시: 문서 접근 로깅
    tracker.log_document_access(
        document_path="roles/business_analyst/deliverables/business_requirements.md",
        role_id="requirements_analyst",
        access_type=AccessType.READ,
        purpose="기술 요구사항 분석을 위한 비즈니스 요구사항 검토",
        duration_seconds=1800,  # 30분
        content_read_percentage=85.0,
        notes="비즈니스 요구사항을 바탕으로 기술적 구현 방안 검토"
    )
    
    print("✅ Document Tracking System 데모 완료")

if __name__ == "__main__":
    main()