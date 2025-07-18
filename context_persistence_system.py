#!/usr/bin/env python3
"""
Context Persistence System for Multi-Agent Claude Code
역할별 히스토리 및 컨텍스트 관리 강화 시스템
"""

import os
import json
import yaml
import sqlite3
import pickle
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from dataclasses import dataclass, asdict
import threading
import logging

class ContextType(Enum):
    """컨텍스트 타입"""
    DECISION_HISTORY = "decision_history"        # 의사결정 이력
    TASK_EXECUTION = "task_execution"            # 작업 실행 기록
    COMMUNICATION = "communication"              # 소통 이력
    LEARNING_OUTCOME = "learning_outcome"        # 학습 결과
    ERROR_PATTERN = "error_pattern"              # 오류 패턴
    SUCCESS_PATTERN = "success_pattern"          # 성공 패턴
    KNOWLEDGE_BASE = "knowledge_base"            # 지식 베이스
    WORKFLOW_STATE = "workflow_state"            # 워크플로우 상태

class ContextScope(Enum):
    """컨텍스트 범위"""
    ROLE_SPECIFIC = "role_specific"              # 역할별
    PROJECT_WIDE = "project_wide"                # 프로젝트 전체
    CROSS_PROJECT = "cross_project"              # 프로젝트 간
    SYSTEM_GLOBAL = "system_global"              # 시스템 전역

@dataclass
class ContextEntry:
    """컨텍스트 엔트리"""
    entry_id: str
    context_type: ContextType
    context_scope: ContextScope
    role_id: str
    project_id: Optional[str]
    timestamp: datetime
    content: Dict[str, Any]
    metadata: Dict[str, Any]
    tags: List[str]
    importance_score: float
    retention_period: Optional[timedelta]
    related_entries: List[str]

@dataclass
class ContextQuery:
    """컨텍스트 쿼리"""
    role_id: Optional[str] = None
    context_types: Optional[List[ContextType]] = None
    time_range: Optional[tuple] = None
    tags: Optional[List[str]] = None
    importance_threshold: Optional[float] = None
    project_id: Optional[str] = None
    content_keywords: Optional[List[str]] = None
    limit: Optional[int] = None

class ContextPersistenceSystem:
    """컨텍스트 지속성 시스템"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.context_dir = self.project_root / "context_storage"
        self.db_path = self.context_dir / "context.db"
        
        # 디렉토리 생성
        self.context_dir.mkdir(exist_ok=True)
        
        # 데이터베이스 초기화
        self._init_database()
        
        # 메모리 캐시
        self.memory_cache: Dict[str, ContextEntry] = {}
        self.cache_lock = threading.Lock()
        
        # 로깅 설정
        self.logger = self._setup_logging()
        
        # 컨텍스트 처리 규칙
        self.processing_rules = self._initialize_processing_rules()
        
        print("🧠 Context Persistence System 초기화 완료")
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS context_entries (
                    entry_id TEXT PRIMARY KEY,
                    context_type TEXT NOT NULL,
                    context_scope TEXT NOT NULL,
                    role_id TEXT NOT NULL,
                    project_id TEXT,
                    timestamp TEXT NOT NULL,
                    content_json TEXT NOT NULL,
                    metadata_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    importance_score REAL NOT NULL,
                    retention_period TEXT,
                    related_entries_json TEXT,
                    content_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_role_type 
                ON context_entries (role_id, context_type)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_timestamp 
                ON context_entries (timestamp)
            ''')
            
            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_importance 
                ON context_entries (importance_score)
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS context_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_entry_id TEXT NOT NULL,
                    to_entry_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (from_entry_id) REFERENCES context_entries (entry_id),
                    FOREIGN KEY (to_entry_id) REFERENCES context_entries (entry_id)
                )
            ''')
    
    def _setup_logging(self) -> logging.Logger:
        """로깅 설정"""
        logger = logging.getLogger('context_persistence')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.FileHandler(self.context_dir / 'context.log')
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _initialize_processing_rules(self) -> Dict[str, Any]:
        """컨텍스트 처리 규칙 초기화"""
        return {
            'importance_calculation': {
                ContextType.DECISION_HISTORY: 0.9,
                ContextType.ERROR_PATTERN: 0.8,
                ContextType.SUCCESS_PATTERN: 0.8,
                ContextType.LEARNING_OUTCOME: 0.7,
                ContextType.TASK_EXECUTION: 0.6,
                ContextType.COMMUNICATION: 0.5,
                ContextType.WORKFLOW_STATE: 0.4,
                ContextType.KNOWLEDGE_BASE: 0.3
            },
            'retention_periods': {
                ContextType.DECISION_HISTORY: timedelta(days=365),
                ContextType.ERROR_PATTERN: timedelta(days=180),
                ContextType.SUCCESS_PATTERN: timedelta(days=180),
                ContextType.LEARNING_OUTCOME: timedelta(days=90),
                ContextType.TASK_EXECUTION: timedelta(days=30),
                ContextType.COMMUNICATION: timedelta(days=30),
                ContextType.WORKFLOW_STATE: timedelta(days=7),
                ContextType.KNOWLEDGE_BASE: None  # 영구 보존
            },
            'auto_tagging_keywords': {
                'critical_decision': ['critical', 'important', 'decision', 'choose', 'select'],
                'error_handling': ['error', 'exception', 'failure', 'bug', 'issue'],
                'performance': ['performance', 'speed', 'optimization', 'efficiency'],
                'quality': ['quality', 'review', 'validation', 'testing', 'standard']
            }
        }
    
    def store_context(self, 
                     role_id: str,
                     context_type: ContextType,
                     content: Dict[str, Any],
                     context_scope: ContextScope = ContextScope.ROLE_SPECIFIC,
                     project_id: Optional[str] = None,
                     custom_tags: List[str] = None,
                     importance_override: Optional[float] = None) -> str:
        """컨텍스트 저장"""
        
        # 엔트리 생성
        entry_id = self._generate_entry_id(role_id, context_type)
        timestamp = datetime.now()
        
        # 중요도 계산
        importance_score = importance_override or self._calculate_importance(context_type, content)
        
        # 자동 태깅
        auto_tags = self._auto_tag_content(content)
        tags = list(set((custom_tags or []) + auto_tags))
        
        # 보존 기간 설정
        retention_period = self.processing_rules['retention_periods'].get(context_type)
        
        # 관련 엔트리 찾기
        related_entries = self._find_related_entries(role_id, context_type, content)
        
        context_entry = ContextEntry(
            entry_id=entry_id,
            context_type=context_type,
            context_scope=context_scope,
            role_id=role_id,
            project_id=project_id,
            timestamp=timestamp,
            content=content,
            metadata={
                'source': 'system_generated',
                'processing_version': '1.0',
                'content_size': len(str(content))
            },
            tags=tags,
            importance_score=importance_score,
            retention_period=retention_period,
            related_entries=related_entries
        )
        
        # 데이터베이스 저장
        self._save_to_database(context_entry)
        
        # 메모리 캐시 업데이트
        with self.cache_lock:
            self.memory_cache[entry_id] = context_entry
        
        # 관계 저장
        self._store_relationships(context_entry)
        
        self.logger.info(f"Context stored: {entry_id} for role {role_id}")
        return entry_id
    
    def retrieve_context(self, query: ContextQuery) -> List[ContextEntry]:
        """컨텍스트 조회"""
        
        # SQL 쿼리 구성
        sql = "SELECT * FROM context_entries WHERE 1=1"
        params = []
        
        if query.role_id:
            sql += " AND role_id = ?"
            params.append(query.role_id)
        
        if query.context_types:
            type_placeholders = ','.join(['?' for _ in query.context_types])
            sql += f" AND context_type IN ({type_placeholders})"
            params.extend([ct.value for ct in query.context_types])
        
        if query.time_range:
            sql += " AND timestamp BETWEEN ? AND ?"
            params.extend([query.time_range[0].isoformat(), query.time_range[1].isoformat()])
        
        if query.importance_threshold:
            sql += " AND importance_score >= ?"
            params.append(query.importance_threshold)
        
        if query.project_id:
            sql += " AND project_id = ?"
            params.append(query.project_id)
        
        # 태그 필터링
        if query.tags:
            for tag in query.tags:
                sql += " AND tags_json LIKE ?"
                params.append(f'%"{tag}"%')
        
        # 키워드 필터링
        if query.content_keywords:
            for keyword in query.content_keywords:
                sql += " AND content_json LIKE ?"
                params.append(f'%{keyword}%')
        
        # 정렬 및 제한
        sql += " ORDER BY importance_score DESC, timestamp DESC"
        
        if query.limit:
            sql += " LIMIT ?"
            params.append(query.limit)
        
        # 쿼리 실행
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
        
        # ContextEntry 객체로 변환
        entries = []
        for row in rows:
            entry = self._row_to_context_entry(row)
            entries.append(entry)
        
        self.logger.info(f"Retrieved {len(entries)} context entries")
        return entries
    
    def get_role_context_summary(self, role_id: str, days_back: int = 30) -> Dict[str, Any]:
        """역할별 컨텍스트 요약"""
        
        # 최근 컨텍스트 조회
        time_range = (datetime.now() - timedelta(days=days_back), datetime.now())
        query = ContextQuery(
            role_id=role_id,
            time_range=time_range
        )
        
        entries = self.retrieve_context(query)
        
        # 요약 생성
        summary = {
            'role_id': role_id,
            'period': f"최근 {days_back}일",
            'total_entries': len(entries),
            'by_type': {},
            'key_decisions': [],
            'learned_patterns': [],
            'frequent_errors': [],
            'success_factors': [],
            'communication_patterns': {},
            'performance_trends': [],
            'recommendations': []
        }
        
        # 타입별 분류
        for entry in entries:
            entry_type = entry.context_type.value
            if entry_type not in summary['by_type']:
                summary['by_type'][entry_type] = 0
            summary['by_type'][entry_type] += 1
        
        # 중요한 의사결정 추출
        decision_entries = [e for e in entries if e.context_type == ContextType.DECISION_HISTORY]
        decision_entries.sort(key=lambda x: x.importance_score, reverse=True)
        for entry in decision_entries[:5]:
            summary['key_decisions'].append({
                'timestamp': entry.timestamp.isoformat(),
                'decision': entry.content.get('decision_summary', 'Unknown'),
                'importance': entry.importance_score
            })
        
        # 학습 패턴 추출
        learning_entries = [e for e in entries if e.context_type == ContextType.LEARNING_OUTCOME]
        for entry in learning_entries[-3:]:  # 최근 3개
            summary['learned_patterns'].append({
                'timestamp': entry.timestamp.isoformat(),
                'pattern': entry.content.get('pattern_description', 'Unknown'),
                'confidence': entry.content.get('confidence_score', 0.0)
            })
        
        # 오류 패턴 분석
        error_entries = [e for e in entries if e.context_type == ContextType.ERROR_PATTERN]
        error_counts = {}
        for entry in error_entries:
            error_type = entry.content.get('error_type', 'unknown')
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        summary['frequent_errors'] = [
            {'error_type': k, 'count': v} 
            for k, v in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        ]
        
        # 성공 요인 분석
        success_entries = [e for e in entries if e.context_type == ContextType.SUCCESS_PATTERN]
        for entry in success_entries[-3:]:
            summary['success_factors'].append({
                'timestamp': entry.timestamp.isoformat(),
                'factor': entry.content.get('success_factor', 'Unknown'),
                'impact': entry.content.get('impact_score', 0.0)
            })
        
        # 권고사항 생성
        summary['recommendations'] = self._generate_recommendations(role_id, entries)
        
        return summary
    
    def store_decision_history(self, 
                             role_id: str,
                             decision_context: Dict[str, Any],
                             decision_made: str,
                             alternatives_considered: List[str],
                             decision_rationale: str,
                             confidence_level: float,
                             project_id: Optional[str] = None) -> str:
        """의사결정 이력 저장"""
        
        content = {
            'decision_context': decision_context,
            'decision_made': decision_made,
            'alternatives_considered': alternatives_considered,
            'decision_rationale': decision_rationale,
            'confidence_level': confidence_level,
            'decision_summary': f"{decision_made} (신뢰도: {confidence_level:.2f})"
        }
        
        return self.store_context(
            role_id=role_id,
            context_type=ContextType.DECISION_HISTORY,
            content=content,
            project_id=project_id,
            custom_tags=['decision', 'critical'] if confidence_level > 0.8 else ['decision'],
            importance_override=0.9 if confidence_level > 0.8 else None
        )
    
    def store_task_execution(self,
                           role_id: str,
                           task_description: str,
                           execution_steps: List[str],
                           execution_result: Dict[str, Any],
                           performance_metrics: Dict[str, Any],
                           project_id: Optional[str] = None) -> str:
        """작업 실행 기록 저장"""
        
        content = {
            'task_description': task_description,
            'execution_steps': execution_steps,
            'execution_result': execution_result,
            'performance_metrics': performance_metrics,
            'success': execution_result.get('success', False),
            'execution_time': performance_metrics.get('execution_time', 0),
            'quality_score': execution_result.get('quality_score', 0.0)
        }
        
        tags = ['task_execution']
        if content['success']:
            tags.append('successful')
        else:
            tags.append('failed')
        
        return self.store_context(
            role_id=role_id,
            context_type=ContextType.TASK_EXECUTION,
            content=content,
            project_id=project_id,
            custom_tags=tags
        )
    
    def store_learning_outcome(self,
                             role_id: str,
                             learning_context: str,
                             pattern_discovered: str,
                             pattern_details: Dict[str, Any],
                             confidence_score: float,
                             applicable_scenarios: List[str],
                             project_id: Optional[str] = None) -> str:
        """학습 결과 저장"""
        
        content = {
            'learning_context': learning_context,
            'pattern_discovered': pattern_discovered,
            'pattern_details': pattern_details,
            'confidence_score': confidence_score,
            'applicable_scenarios': applicable_scenarios,
            'pattern_description': f"{pattern_discovered} (신뢰도: {confidence_score:.2f})"
        }
        
        return self.store_context(
            role_id=role_id,
            context_type=ContextType.LEARNING_OUTCOME,
            content=content,
            project_id=project_id,
            custom_tags=['learning', 'pattern', 'intelligence']
        )
    
    def store_error_pattern(self,
                          role_id: str,
                          error_type: str,
                          error_details: Dict[str, Any],
                          occurrence_frequency: int,
                          resolution_steps: List[str],
                          prevention_strategies: List[str],
                          project_id: Optional[str] = None) -> str:
        """오류 패턴 저장"""
        
        content = {
            'error_type': error_type,
            'error_details': error_details,
            'occurrence_frequency': occurrence_frequency,
            'resolution_steps': resolution_steps,
            'prevention_strategies': prevention_strategies,
            'severity': error_details.get('severity', 'medium')
        }
        
        tags = ['error', 'pattern']
        if content['severity'] == 'high':
            tags.append('critical')
        
        return self.store_context(
            role_id=role_id,
            context_type=ContextType.ERROR_PATTERN,
            content=content,
            project_id=project_id,
            custom_tags=tags,
            importance_override=0.9 if content['severity'] == 'high' else None
        )
    
    def get_relevant_context_for_task(self, 
                                    role_id: str,
                                    current_task_description: str,
                                    max_entries: int = 10) -> List[ContextEntry]:
        """현재 작업에 관련된 컨텍스트 조회"""
        
        # 키워드 추출
        keywords = self._extract_keywords(current_task_description)
        
        # 관련 컨텍스트 쿼리
        query = ContextQuery(
            role_id=role_id,
            content_keywords=keywords[:5],  # 상위 5개 키워드
            importance_threshold=0.3,
            limit=max_entries * 2  # 필터링을 위해 더 많이 조회
        )
        
        entries = self.retrieve_context(query)
        
        # 관련성 점수 계산 및 정렬
        scored_entries = []
        for entry in entries:
            relevance_score = self._calculate_relevance_score(
                current_task_description, entry
            )
            scored_entries.append((entry, relevance_score))
        
        # 관련성 점수 기준 정렬
        scored_entries.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 항목 반환
        return [entry for entry, score in scored_entries[:max_entries]]
    
    # Helper methods
    def _generate_entry_id(self, role_id: str, context_type: ContextType) -> str:
        """엔트리 ID 생성"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        return f"{role_id}_{context_type.value}_{timestamp}"
    
    def _calculate_importance(self, context_type: ContextType, content: Dict[str, Any]) -> float:
        """중요도 계산"""
        base_importance = self.processing_rules['importance_calculation'].get(context_type, 0.5)
        
        # 컨텐츠 기반 조정
        adjustments = 0.0
        
        # 성공/실패에 따른 조정
        if content.get('success') is False:
            adjustments += 0.1  # 실패는 학습 기회
        elif content.get('success') is True:
            adjustments += 0.05  # 성공도 중요
        
        # 신뢰도/품질 점수에 따른 조정
        confidence = content.get('confidence_level') or content.get('confidence_score', 0.5)
        if confidence > 0.8:
            adjustments += 0.1
        
        quality_score = content.get('quality_score', 0.5)
        if quality_score > 0.8:
            adjustments += 0.05
        
        return min(1.0, base_importance + adjustments)
    
    def _auto_tag_content(self, content: Dict[str, Any]) -> List[str]:
        """컨텐츠 자동 태깅"""
        tags = []
        content_text = str(content).lower()
        
        for tag, keywords in self.processing_rules['auto_tagging_keywords'].items():
            if any(keyword in content_text for keyword in keywords):
                tags.append(tag)
        
        return tags
    
    def _find_related_entries(self, 
                            role_id: str, 
                            context_type: ContextType, 
                            content: Dict[str, Any]) -> List[str]:
        """관련 엔트리 찾기"""
        # 간단한 구현 - 실제로는 더 정교한 유사성 분석 필요
        keywords = self._extract_keywords(str(content))[:3]
        
        if not keywords:
            return []
        
        query = ContextQuery(
            role_id=role_id,
            content_keywords=keywords,
            limit=5
        )
        
        related_entries = self.retrieve_context(query)
        return [entry.entry_id for entry in related_entries[-5:]]  # 최근 5개
    
    def _extract_keywords(self, text: str) -> List[str]:
        """키워드 추출"""
        # 간단한 키워드 추출 - 실제로는 NLP 라이브러리 사용 권장
        words = text.lower().split()
        
        # 불용어 제거
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 3 and word not in stop_words]
        
        # 빈도 기반 정렬 (간단한 구현)
        from collections import Counter
        word_counts = Counter(keywords)
        
        return [word for word, count in word_counts.most_common(10)]
    
    def _calculate_relevance_score(self, task_description: str, entry: ContextEntry) -> float:
        """관련성 점수 계산"""
        task_keywords = set(self._extract_keywords(task_description))
        entry_keywords = set(self._extract_keywords(str(entry.content)))
        
        # 키워드 교집합 기반 관련성
        if not task_keywords or not entry_keywords:
            return 0.0
        
        intersection = len(task_keywords & entry_keywords)
        union = len(task_keywords | entry_keywords)
        
        keyword_similarity = intersection / union if union > 0 else 0.0
        
        # 중요도와 시간 가중치 적용
        time_weight = max(0.1, 1.0 - (datetime.now() - entry.timestamp).days / 365)
        
        return keyword_similarity * entry.importance_score * time_weight
    
    def _save_to_database(self, entry: ContextEntry):
        """데이터베이스에 저장"""
        content_hash = hashlib.md5(str(entry.content).encode()).hexdigest()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO context_entries 
                (entry_id, context_type, context_scope, role_id, project_id, timestamp,
                 content_json, metadata_json, tags_json, importance_score, 
                 retention_period, related_entries_json, content_hash, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                entry.entry_id,
                entry.context_type.value,
                entry.context_scope.value,
                entry.role_id,
                entry.project_id,
                entry.timestamp.isoformat(),
                json.dumps(entry.content, ensure_ascii=False),
                json.dumps(entry.metadata, ensure_ascii=False),
                json.dumps(entry.tags, ensure_ascii=False),
                entry.importance_score,
                entry.retention_period.total_seconds() if entry.retention_period else None,
                json.dumps(entry.related_entries, ensure_ascii=False),
                content_hash,
                datetime.now().isoformat()
            ))
    
    def _store_relationships(self, entry: ContextEntry):
        """관계 저장"""
        if not entry.related_entries:
            return
        
        with sqlite3.connect(self.db_path) as conn:
            for related_id in entry.related_entries:
                conn.execute('''
                    INSERT INTO context_relationships 
                    (from_entry_id, to_entry_id, relationship_type, strength, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    entry.entry_id,
                    related_id,
                    'content_similarity',
                    0.7,  # 기본 강도
                    datetime.now().isoformat()
                ))
    
    def _row_to_context_entry(self, row: sqlite3.Row) -> ContextEntry:
        """데이터베이스 행을 ContextEntry로 변환"""
        return ContextEntry(
            entry_id=row['entry_id'],
            context_type=ContextType(row['context_type']),
            context_scope=ContextScope(row['context_scope']),
            role_id=row['role_id'],
            project_id=row['project_id'],
            timestamp=datetime.fromisoformat(row['timestamp']),
            content=json.loads(row['content_json']),
            metadata=json.loads(row['metadata_json']),
            tags=json.loads(row['tags_json']),
            importance_score=row['importance_score'],
            retention_period=timedelta(seconds=row['retention_period']) if row['retention_period'] else None,
            related_entries=json.loads(row['related_entries_json'])
        )
    
    def _generate_recommendations(self, role_id: str, entries: List[ContextEntry]) -> List[str]:
        """권고사항 생성"""
        recommendations = []
        
        # 오류 패턴 기반 권고
        error_entries = [e for e in entries if e.context_type == ContextType.ERROR_PATTERN]
        if len(error_entries) > 3:
            recommendations.append("반복되는 오류 패턴이 발견되었습니다. 예방 전략을 강화하세요.")
        
        # 성공 패턴 기반 권고
        success_entries = [e for e in entries if e.context_type == ContextType.SUCCESS_PATTERN]
        if success_entries:
            recommendations.append("성공적인 패턴을 다른 작업에도 적용해보세요.")
        
        # 의사결정 패턴 분석
        decision_entries = [e for e in entries if e.context_type == ContextType.DECISION_HISTORY]
        low_confidence_decisions = [e for e in decision_entries if e.content.get('confidence_level', 1.0) < 0.6]
        if len(low_confidence_decisions) > 2:
            recommendations.append("신뢰도가 낮은 의사결정이 많습니다. 더 많은 정보 수집을 고려하세요.")
        
        return recommendations

def main():
    """테스트 및 데모"""
    context_system = ContextPersistenceSystem("/home/jungh/workspace/multi_claude_code_sample")
    
    # 예시 1: 의사결정 이력 저장
    decision_id = context_system.store_decision_history(
        role_id="business_analyst",
        decision_context={
            "situation": "API 버전 선택",
            "constraints": ["성능 요구사항", "호환성", "보안"],
            "stakeholders": ["개발팀", "운영팀"]
        },
        decision_made="REST API v2.0 사용",
        alternatives_considered=["GraphQL", "REST API v1.0", "gRPC"],
        decision_rationale="성능과 호환성의 균형이 가장 좋음",
        confidence_level=0.85,
        project_id="web_community"
    )
    print(f"✅ 의사결정 이력 저장: {decision_id}")
    
    # 예시 2: 작업 실행 기록 저장
    task_id = context_system.store_task_execution(
        role_id="frontend_developer",
        task_description="사용자 로그인 폼 구현",
        execution_steps=[
            "요구사항 분석",
            "UI 컴포넌트 설계",
            "폼 검증 로직 구현",
            "API 통합",
            "테스트 수행"
        ],
        execution_result={
            "success": True,
            "deliverable_path": "/src/components/LoginForm.tsx",
            "quality_score": 0.92
        },
        performance_metrics={
            "execution_time": 240,  # 분
            "code_coverage": 0.85,
            "bugs_found": 1
        },
        project_id="web_community"
    )
    print(f"✅ 작업 실행 기록 저장: {task_id}")
    
    # 예시 3: 학습 결과 저장
    learning_id = context_system.store_learning_outcome(
        role_id="qa_tester",
        learning_context="자동화 테스트 실행 중 발견된 패턴",
        pattern_discovered="API 응답 시간이 DB 쿼리 복잡도와 강한 상관관계",
        pattern_details={
            "correlation_coefficient": 0.87,
            "sample_size": 150,
            "statistical_significance": 0.001
        },
        confidence_score=0.9,
        applicable_scenarios=["성능 테스트", "API 최적화", "데이터베이스 튜닝"],
        project_id="web_community"
    )
    print(f"✅ 학습 결과 저장: {learning_id}")
    
    # 예시 4: 역할별 컨텍스트 요약 조회
    summary = context_system.get_role_context_summary("business_analyst", days_back=7)
    print("📊 Business Analyst 컨텍스트 요약:")
    print(f"  - 총 엔트리: {summary['total_entries']}")
    print(f"  - 주요 의사결정: {len(summary['key_decisions'])}개")
    print(f"  - 권고사항: {len(summary['recommendations'])}개")
    
    # 예시 5: 현재 작업 관련 컨텍스트 조회
    relevant_context = context_system.get_relevant_context_for_task(
        role_id="frontend_developer",
        current_task_description="사용자 대시보드 컴포넌트 구현",
        max_entries=5
    )
    print(f"🔍 관련 컨텍스트 {len(relevant_context)}개 발견")

if __name__ == "__main__":
    main()