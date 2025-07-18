#!/usr/bin/env python3
"""
Smart File Discovery System for Multi-Agent Claude Code
지능적 파일 탐색 및 메타데이터 시스템
"""

import os
import json
import yaml
import hashlib
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from enum import Enum
from dataclasses import dataclass, asdict
import sqlite3
import threading
import time
import fnmatch
import re

class FileType(Enum):
    """파일 타입"""
    SOURCE_CODE = "source_code"
    DOCUMENTATION = "documentation"
    CONFIGURATION = "configuration"
    DATA = "data"
    TEMPLATE = "template"
    SPECIFICATION = "specification"
    TEST = "test"
    BUILD_ARTIFACT = "build_artifact"
    MEDIA = "media"
    UNKNOWN = "unknown"

class FileStatus(Enum):
    """파일 상태"""
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"
    DELETED = "deleted"
    DRAFT = "draft"
    REVIEW = "review"

class AccessPattern(Enum):
    """접근 패턴"""
    FREQUENT = "frequent"
    OCCASIONAL = "occasional"
    RARE = "rare"
    NEVER_ACCESSED = "never_accessed"

@dataclass
class FileMetadata:
    """파일 메타데이터"""
    file_path: str
    file_name: str
    file_type: FileType
    file_status: FileStatus
    size_bytes: int
    created_at: datetime
    modified_at: datetime
    last_accessed: Optional[datetime]
    access_count: int
    access_pattern: AccessPattern
    content_hash: str
    mime_type: str
    encoding: Optional[str]
    language: Optional[str]
    framework: Optional[str]
    dependencies: List[str]
    tags: List[str]
    purpose: Optional[str]
    role_ownership: Optional[str]
    project_phase: Optional[str]
    quality_score: float
    complexity_score: float
    maintainability_score: float

@dataclass
class FileRelationship:
    """파일 간 관계"""
    from_file: str
    to_file: str
    relationship_type: str  # "imports", "includes", "references", "generates", "tests"
    strength: float
    discovered_at: datetime

@dataclass
class SearchQuery:
    """검색 쿼리"""
    keywords: Optional[List[str]] = None
    file_types: Optional[List[FileType]] = None
    roles: Optional[List[str]] = None
    project_phases: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    modified_since: Optional[datetime] = None
    size_range: Optional[Tuple[int, int]] = None
    quality_threshold: Optional[float] = None
    access_pattern: Optional[AccessPattern] = None
    content_regex: Optional[str] = None
    exclude_patterns: Optional[List[str]] = None
    limit: Optional[int] = None

class SmartFileDiscoverySystem:
    """지능적 파일 발견 시스템"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.discovery_dir = self.project_root / "file_discovery"
        self.metadata_db = self.discovery_dir / "file_metadata.db"
        
        # 디렉토리 생성
        self.discovery_dir.mkdir(exist_ok=True)
        
        # 데이터베이스 초기화
        self._init_database()
        
        # 파일 탐지 규칙
        self.detection_rules = self._initialize_detection_rules()
        
        # 캐시
        self.metadata_cache: Dict[str, FileMetadata] = {}
        self.cache_lock = threading.Lock()
        
        # 백그라운드 스캔 설정
        self.scan_active = True
        self.last_scan_time = datetime.min
        
        # 실시간 모니터링 스레드
        self.monitor_thread = threading.Thread(target=self._monitor_file_changes, daemon=True)
        self.monitor_thread.start()
        
        print("🔍 Smart File Discovery System 초기화 완료")
    
    def _init_database(self):
        """데이터베이스 초기화"""
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_metadata (
                    file_path TEXT PRIMARY KEY,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_status TEXT NOT NULL,
                    size_bytes INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    modified_at TEXT NOT NULL,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    access_pattern TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    mime_type TEXT NOT NULL,
                    encoding TEXT,
                    language TEXT,
                    framework TEXT,
                    dependencies TEXT,  -- JSON array
                    tags TEXT,          -- JSON array
                    purpose TEXT,
                    role_ownership TEXT,
                    project_phase TEXT,
                    quality_score REAL DEFAULT 0.5,
                    complexity_score REAL DEFAULT 0.5,
                    maintainability_score REAL DEFAULT 0.5,
                    indexed_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS file_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_file TEXT NOT NULL,
                    to_file TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL NOT NULL,
                    discovered_at TEXT NOT NULL,
                    FOREIGN KEY (from_file) REFERENCES file_metadata (file_path),
                    FOREIGN KEY (to_file) REFERENCES file_metadata (file_path)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS access_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    accessed_by TEXT NOT NULL,
                    access_type TEXT NOT NULL,  -- read, write, execute
                    accessed_at TEXT NOT NULL,
                    FOREIGN KEY (file_path) REFERENCES file_metadata (file_path)
                )
            ''')
            
            # 인덱스 생성
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file_type ON file_metadata (file_type)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_file_status ON file_metadata (file_status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_modified_at ON file_metadata (modified_at)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_role_ownership ON file_metadata (role_ownership)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_project_phase ON file_metadata (project_phase)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_quality_score ON file_metadata (quality_score)')
    
    def _initialize_detection_rules(self) -> Dict[str, Any]:
        """파일 탐지 규칙 초기화"""
        return {
            'file_type_patterns': {
                FileType.SOURCE_CODE: [
                    '*.py', '*.js', '*.ts', '*.tsx', '*.jsx', '*.java', '*.cpp', '*.c', '*.cs', 
                    '*.go', '*.rs', '*.rb', '*.php', '*.swift', '*.kt', '*.scala', '*.clj'
                ],
                FileType.DOCUMENTATION: [
                    '*.md', '*.rst', '*.txt', '*.doc', '*.docx', '*.pdf', 'README*', 'CHANGELOG*',
                    'CONTRIBUTING*', 'LICENSE*', '*.wiki'
                ],
                FileType.CONFIGURATION: [
                    '*.json', '*.yaml', '*.yml', '*.toml', '*.ini', '*.cfg', '*.conf',
                    '*.properties', '.env*', 'Dockerfile*', '*.dockerfile'
                ],
                FileType.DATA: [
                    '*.csv', '*.json', '*.xml', '*.sql', '*.db', '*.sqlite', '*.sqlite3',
                    '*.parquet', '*.avro', '*.jsonl'
                ],
                FileType.TEMPLATE: [
                    '*.jinja', '*.j2', '*.template', '*.tmpl', '*.tpl', '*.mustache', '*.hbs'
                ],
                FileType.SPECIFICATION: [
                    '*spec.md', '*specification.md', '*requirements.md', '*.proto', '*.avsc',
                    '*.openapi', '*.swagger', '*-spec.json', '*-specification.json'
                ],
                FileType.TEST: [
                    '*test*.py', '*_test.py', 'test_*.py', '*test*.js', '*test*.ts',
                    '*spec*.py', '*spec*.js', '*spec*.ts', '*.test.*'
                ],
                FileType.BUILD_ARTIFACT: [
                    '*.jar', '*.war', '*.ear', '*.tar', '*.zip', '*.gz', '*.bz2',
                    'dist/*', 'build/*', 'target/*', 'node_modules/*'
                ],
                FileType.MEDIA: [
                    '*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg', '*.ico', '*.webp',
                    '*.mp4', '*.avi', '*.mov', '*.mp3', '*.wav'
                ]
            },
            'language_detection': {
                '.py': 'Python',
                '.js': 'JavaScript',
                '.ts': 'TypeScript',
                '.tsx': 'TypeScript',
                '.jsx': 'JavaScript',
                '.java': 'Java',
                '.cpp': 'C++',
                '.c': 'C',
                '.cs': 'C#',
                '.go': 'Go',
                '.rs': 'Rust',
                '.rb': 'Ruby',
                '.php': 'PHP',
                '.swift': 'Swift',
                '.kt': 'Kotlin',
                '.scala': 'Scala',
                '.clj': 'Clojure'
            },
            'framework_detection': {
                'package.json': ['React', 'Vue', 'Angular', 'Express', 'Next.js'],
                'requirements.txt': ['Django', 'Flask', 'FastAPI', 'Pandas'],
                'Gemfile': ['Rails', 'Sinatra'],
                'composer.json': ['Laravel', 'Symfony'],
                'pom.xml': ['Spring', 'Maven'],
                'build.gradle': ['Spring Boot', 'Android']
            },
            'exclude_patterns': [
                '*.pyc', '__pycache__/*', '.git/*', '.svn/*', '.hg/*',
                'node_modules/*', 'venv/*', '.venv/*', 'env/*',
                '*.log', '*.tmp', '*.cache', '.DS_Store', 'Thumbs.db'
            ],
            'quality_indicators': {
                'high_quality': ['test', 'spec', 'documentation', 'readme'],
                'complexity_keywords': ['if', 'for', 'while', 'switch', 'case', 'try', 'catch'],
                'maintainability_keywords': ['class', 'function', 'def', 'interface', 'abstract']
            }
        }
    
    def scan_project_files(self, force_rescan: bool = False) -> Dict[str, Any]:
        """프로젝트 파일 전체 스캔"""
        
        start_time = datetime.now()
        
        # 이미 최근에 스캔했고 강제 재스캔이 아닌 경우 스킵
        if not force_rescan and (start_time - self.last_scan_time) < timedelta(hours=1):
            return {"status": "skipped", "reason": "Recent scan exists"}
        
        scan_results = {
            "start_time": start_time.isoformat(),
            "files_discovered": 0,
            "files_updated": 0,
            "files_deleted": 0,
            "relationships_found": 0,
            "errors": []
        }
        
        try:
            # 현재 파일들 스캔
            current_files = set()
            
            for file_path in self._scan_directory(self.project_root):
                try:
                    current_files.add(str(file_path))
                    
                    # 파일이 제외 패턴에 해당하는지 확인
                    if self._should_exclude_file(file_path):
                        continue
                    
                    # 메타데이터 생성/업데이트
                    metadata = self._analyze_file(file_path)
                    if metadata:
                        if self._is_new_or_modified(metadata):
                            self._save_file_metadata(metadata)
                            scan_results["files_updated"] += 1
                        scan_results["files_discovered"] += 1
                    
                except Exception as e:
                    scan_results["errors"].append(f"Error processing {file_path}: {str(e)}")
            
            # 삭제된 파일 확인
            existing_files = self._get_all_tracked_files()
            deleted_files = set(existing_files) - current_files
            
            for deleted_file in deleted_files:
                self._mark_file_deleted(deleted_file)
                scan_results["files_deleted"] += 1
            
            # 파일 간 관계 분석
            relationships_found = self._analyze_file_relationships(current_files)
            scan_results["relationships_found"] = relationships_found
            
            # 스캔 완료 시간 업데이트
            self.last_scan_time = start_time
            
            scan_results["end_time"] = datetime.now().isoformat()
            scan_results["duration_seconds"] = (datetime.now() - start_time).total_seconds()
            scan_results["status"] = "completed"
            
            print(f"📁 파일 스캔 완료: {scan_results['files_discovered']}개 발견, {scan_results['files_updated']}개 업데이트")
            
        except Exception as e:
            scan_results["status"] = "failed"
            scan_results["error"] = str(e)
            print(f"⚠️ 파일 스캔 실패: {str(e)}")
        
        return scan_results
    
    def smart_search(self, query: SearchQuery) -> List[FileMetadata]:
        """지능적 파일 검색"""
        
        # SQL 쿼리 구성
        sql = "SELECT * FROM file_metadata WHERE file_status != 'deleted'"
        params = []
        
        # 키워드 검색
        if query.keywords:
            keyword_conditions = []
            for keyword in query.keywords:
                keyword_conditions.append("(file_name LIKE ? OR purpose LIKE ? OR tags LIKE ?)")
                params.extend([f'%{keyword}%', f'%{keyword}%', f'%{keyword}%'])
            sql += f" AND ({' OR '.join(keyword_conditions)})"
        
        # 파일 타입 필터
        if query.file_types:
            type_placeholders = ','.join(['?' for _ in query.file_types])
            sql += f" AND file_type IN ({type_placeholders})"
            params.extend([ft.value for ft in query.file_types])
        
        # 역할 필터
        if query.roles:
            role_placeholders = ','.join(['?' for _ in query.roles])
            sql += f" AND role_ownership IN ({role_placeholders})"
            params.extend(query.roles)
        
        # 프로젝트 단계 필터
        if query.project_phases:
            phase_placeholders = ','.join(['?' for _ in query.project_phases])
            sql += f" AND project_phase IN ({phase_placeholders})"
            params.extend(query.project_phases)
        
        # 수정 시간 필터
        if query.modified_since:
            sql += " AND modified_at >= ?"
            params.append(query.modified_since.isoformat())
        
        # 크기 범위 필터
        if query.size_range:
            sql += " AND size_bytes BETWEEN ? AND ?"
            params.extend(query.size_range)
        
        # 품질 임계값 필터
        if query.quality_threshold:
            sql += " AND quality_score >= ?"
            params.append(query.quality_threshold)
        
        # 접근 패턴 필터
        if query.access_pattern:
            sql += " AND access_pattern = ?"
            params.append(query.access_pattern.value)
        
        # 태그 필터
        if query.tags:
            for tag in query.tags:
                sql += " AND tags LIKE ?"
                params.append(f'%"{tag}"%')
        
        # 정렬
        sql += " ORDER BY quality_score DESC, modified_at DESC"
        
        # 제한
        if query.limit:
            sql += " LIMIT ?"
            params.append(query.limit)
        
        # 쿼리 실행
        with sqlite3.connect(self.metadata_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(sql, params)
            rows = cursor.fetchall()
        
        # FileMetadata 객체로 변환
        results = []
        for row in rows:
            metadata = self._row_to_file_metadata(row)
            
            # 컨텐츠 정규식 필터 (파일이 존재하는 경우)
            if query.content_regex and Path(metadata.file_path).exists():
                if not self._content_matches_regex(metadata.file_path, query.content_regex):
                    continue
            
            # 제외 패턴 확인
            if query.exclude_patterns:
                if any(fnmatch.fnmatch(metadata.file_path, pattern) for pattern in query.exclude_patterns):
                    continue
            
            results.append(metadata)
        
        return results
    
    def suggest_relevant_files(self, 
                             role_id: str,
                             current_task: str,
                             max_suggestions: int = 10) -> List[Tuple[FileMetadata, float]]:
        """관련 파일 제안"""
        
        # 현재 작업에서 키워드 추출
        keywords = self._extract_keywords_from_task(current_task)
        
        # 역할 기반 검색
        base_query = SearchQuery(
            keywords=keywords[:5],
            roles=[role_id],
            file_types=[FileType.SOURCE_CODE, FileType.DOCUMENTATION, FileType.SPECIFICATION],
            quality_threshold=0.3,
            limit=max_suggestions * 2
        )
        
        candidates = self.smart_search(base_query)
        
        # 관련성 점수 계산
        scored_files = []
        for file_metadata in candidates:
            relevance_score = self._calculate_file_relevance(current_task, file_metadata)
            scored_files.append((file_metadata, relevance_score))
        
        # 점수 기준 정렬
        scored_files.sort(key=lambda x: x[1], reverse=True)
        
        return scored_files[:max_suggestions]
    
    def get_file_dependencies(self, file_path: str) -> List[FileRelationship]:
        """파일 의존성 조회"""
        
        with sqlite3.connect(self.metadata_db) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM file_relationships 
                WHERE from_file = ? OR to_file = ?
                ORDER BY strength DESC
            ''', (file_path, file_path))
            
            relationships = []
            for row in cursor.fetchall():
                relationships.append(FileRelationship(
                    from_file=row['from_file'],
                    to_file=row['to_file'],
                    relationship_type=row['relationship_type'],
                    strength=row['strength'],
                    discovered_at=datetime.fromisoformat(row['discovered_at'])
                ))
        
        return relationships
    
    def track_file_access(self, file_path: str, accessed_by: str, access_type: str = "read"):
        """파일 접근 추적"""
        
        # 접근 로그 저장
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute('''
                INSERT INTO access_log (file_path, accessed_by, access_type, accessed_at)
                VALUES (?, ?, ?, ?)
            ''', (file_path, accessed_by, access_type, datetime.now().isoformat()))
            
            # 파일 메타데이터 업데이트
            conn.execute('''
                UPDATE file_metadata 
                SET access_count = access_count + 1,
                    last_accessed = ?
                WHERE file_path = ?
            ''', (datetime.now().isoformat(), file_path))
        
        # 접근 패턴 업데이트
        self._update_access_pattern(file_path)
    
    def get_project_file_overview(self) -> Dict[str, Any]:
        """프로젝트 파일 개요"""
        
        with sqlite3.connect(self.metadata_db) as conn:
            # 전체 통계
            total_files = conn.execute("SELECT COUNT(*) FROM file_metadata WHERE file_status != 'deleted'").fetchone()[0]
            
            # 타입별 분포
            type_distribution = {}
            cursor = conn.execute('''
                SELECT file_type, COUNT(*) as count 
                FROM file_metadata 
                WHERE file_status != 'deleted'
                GROUP BY file_type
            ''')
            for row in cursor.fetchall():
                type_distribution[row[0]] = row[1]
            
            # 역할별 분포
            role_distribution = {}
            cursor = conn.execute('''
                SELECT role_ownership, COUNT(*) as count 
                FROM file_metadata 
                WHERE file_status != 'deleted' AND role_ownership IS NOT NULL
                GROUP BY role_ownership
            ''')
            for row in cursor.fetchall():
                role_distribution[row[0]] = row[1]
            
            # 품질 분포
            quality_stats = conn.execute('''
                SELECT 
                    AVG(quality_score) as avg_quality,
                    MIN(quality_score) as min_quality,
                    MAX(quality_score) as max_quality
                FROM file_metadata 
                WHERE file_status != 'deleted'
            ''').fetchone()
            
            # 최근 활동
            recent_files = conn.execute('''
                SELECT file_path, modified_at 
                FROM file_metadata 
                WHERE file_status != 'deleted'
                ORDER BY modified_at DESC 
                LIMIT 10
            ''').fetchall()
            
            # 접근 패턴
            access_patterns = {}
            cursor = conn.execute('''
                SELECT access_pattern, COUNT(*) as count 
                FROM file_metadata 
                WHERE file_status != 'deleted'
                GROUP BY access_pattern
            ''')
            for row in cursor.fetchall():
                access_patterns[row[0]] = row[1]
        
        return {
            'total_files': total_files,
            'type_distribution': type_distribution,
            'role_distribution': role_distribution,
            'quality_statistics': {
                'average_quality': quality_stats[0] or 0.0,
                'min_quality': quality_stats[1] or 0.0,
                'max_quality': quality_stats[2] or 0.0
            },
            'recent_activity': [
                {'file_path': row[0], 'modified_at': row[1]}
                for row in recent_files
            ],
            'access_patterns': access_patterns,
            'last_scan': self.last_scan_time.isoformat() if self.last_scan_time != datetime.min else None
        }
    
    # Helper methods
    def _scan_directory(self, directory: Path):
        """디렉토리 재귀 스캔"""
        for item in directory.rglob('*'):
            if item.is_file():
                yield item
    
    def _should_exclude_file(self, file_path: Path) -> bool:
        """파일 제외 여부 확인"""
        file_str = str(file_path)
        return any(fnmatch.fnmatch(file_str, pattern) for pattern in self.detection_rules['exclude_patterns'])
    
    def _analyze_file(self, file_path: Path) -> Optional[FileMetadata]:
        """파일 분석"""
        try:
            if not file_path.exists():
                return None
            
            stat = file_path.stat()
            
            # 기본 정보
            file_name = file_path.name
            size_bytes = stat.st_size
            created_at = datetime.fromtimestamp(stat.st_ctime)
            modified_at = datetime.fromtimestamp(stat.st_mtime)
            
            # 파일 타입 감지
            file_type = self._detect_file_type(file_path)
            
            # 콘텐츠 해시
            content_hash = self._calculate_file_hash(file_path)
            
            # MIME 타입
            mime_type, _ = mimetypes.guess_type(str(file_path))
            mime_type = mime_type or 'application/octet-stream'
            
            # 언어 감지
            language = self._detect_language(file_path)
            
            # 프레임워크 감지
            framework = self._detect_framework(file_path)
            
            # 의존성 추출
            dependencies = self._extract_dependencies(file_path)
            
            # 태그 생성
            tags = self._generate_file_tags(file_path, file_type)
            
            # 목적 추론
            purpose = self._infer_file_purpose(file_path, file_type)
            
            # 역할 소유권 추론
            role_ownership = self._infer_role_ownership(file_path)
            
            # 프로젝트 단계 추론
            project_phase = self._infer_project_phase(file_path, file_type)
            
            # 품질 점수 계산
            quality_score = self._calculate_quality_score(file_path, file_type)
            
            # 복잡도 점수 계산
            complexity_score = self._calculate_complexity_score(file_path, file_type)
            
            # 유지보수성 점수 계산
            maintainability_score = self._calculate_maintainability_score(file_path, file_type)
            
            return FileMetadata(
                file_path=str(file_path),
                file_name=file_name,
                file_type=file_type,
                file_status=FileStatus.ACTIVE,
                size_bytes=size_bytes,
                created_at=created_at,
                modified_at=modified_at,
                last_accessed=None,
                access_count=0,
                access_pattern=AccessPattern.NEVER_ACCESSED,
                content_hash=content_hash,
                mime_type=mime_type,
                encoding=None,
                language=language,
                framework=framework,
                dependencies=dependencies,
                tags=tags,
                purpose=purpose,
                role_ownership=role_ownership,
                project_phase=project_phase,
                quality_score=quality_score,
                complexity_score=complexity_score,
                maintainability_score=maintainability_score
            )
            
        except Exception as e:
            print(f"파일 분석 오류 ({file_path}): {str(e)}")
            return None
    
    def _detect_file_type(self, file_path: Path) -> FileType:
        """파일 타입 감지"""
        file_str = str(file_path).lower()
        
        for file_type, patterns in self.detection_rules['file_type_patterns'].items():
            if any(fnmatch.fnmatch(file_str, pattern.lower()) for pattern in patterns):
                return file_type
        
        return FileType.UNKNOWN
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """파일 해시 계산"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except:
            return ""
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """프로그래밍 언어 감지"""
        suffix = file_path.suffix.lower()
        return self.detection_rules['language_detection'].get(suffix)
    
    def _detect_framework(self, file_path: Path) -> Optional[str]:
        """프레임워크 감지"""
        # 간단한 구현 - 실제로는 더 정교한 분석 필요
        file_name = file_path.name.lower()
        
        for config_file, frameworks in self.detection_rules['framework_detection'].items():
            if config_file in file_name:
                return frameworks[0] if frameworks else None
        
        return None
    
    def _extract_dependencies(self, file_path: Path) -> List[str]:
        """의존성 추출"""
        dependencies = []
        
        try:
            if file_path.suffix.lower() == '.py':
                # Python import 분석
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                import_patterns = [
                    r'import\s+([a-zA-Z_][a-zA-Z0-9_]*)',
                    r'from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import'
                ]
                
                for pattern in import_patterns:
                    matches = re.findall(pattern, content)
                    dependencies.extend(matches)
                    
        except Exception:
            pass
        
        return list(set(dependencies))
    
    def _generate_file_tags(self, file_path: Path, file_type: FileType) -> List[str]:
        """파일 태그 생성"""
        tags = [file_type.value]
        
        file_name_lower = file_path.name.lower()
        
        # 특별한 파일들에 대한 태그
        if 'test' in file_name_lower:
            tags.append('test')
        if 'config' in file_name_lower:
            tags.append('configuration')
        if 'readme' in file_name_lower:
            tags.append('documentation')
        if 'api' in file_name_lower:
            tags.append('api')
        if 'util' in file_name_lower or 'helper' in file_name_lower:
            tags.append('utility')
        
        # 경로 기반 태그
        path_parts = file_path.parts
        if 'src' in path_parts:
            tags.append('source')
        if 'test' in path_parts:
            tags.append('test')
        if 'doc' in path_parts or 'docs' in path_parts:
            tags.append('documentation')
        
        return list(set(tags))
    
    def _infer_file_purpose(self, file_path: Path, file_type: FileType) -> Optional[str]:
        """파일 목적 추론"""
        file_name = file_path.name.lower()
        
        purpose_mapping = {
            'main': '메인 진입점',
            'index': '인덱스 파일',
            'config': '설정 파일',
            'test': '테스트 파일',
            'util': '유틸리티 함수',
            'helper': '헬퍼 함수',
            'model': '데이터 모델',
            'view': '뷰 컴포넌트',
            'controller': '컨트롤러',
            'service': '서비스 로직',
            'api': 'API 인터페이스',
            'component': 'UI 컴포넌트'
        }
        
        for keyword, purpose in purpose_mapping.items():
            if keyword in file_name:
                return purpose
        
        return None
    
    def _infer_role_ownership(self, file_path: Path) -> Optional[str]:
        """역할 소유권 추론"""
        path_str = str(file_path).lower()
        
        role_indicators = {
            'frontend': ['frontend', 'ui', 'component', 'view', 'css', 'html'],
            'backend': ['backend', 'api', 'server', 'service', 'model'],
            'qa_tester': ['test', 'spec', 'testing'],
            'devops': ['deploy', 'docker', 'kubernetes', 'ci', 'cd'],
            'database_designer': ['migration', 'schema', 'database', 'sql'],
            'business_analyst': ['requirement', 'spec', 'business']
        }
        
        for role, indicators in role_indicators.items():
            if any(indicator in path_str for indicator in indicators):
                return role
        
        return None
    
    def _infer_project_phase(self, file_path: Path, file_type: FileType) -> Optional[str]:
        """프로젝트 단계 추론"""
        if file_type == FileType.SPECIFICATION:
            return 'planning'
        elif file_type == FileType.SOURCE_CODE:
            return 'development'
        elif file_type == FileType.TEST:
            return 'testing'
        elif file_type == FileType.CONFIGURATION and 'deploy' in str(file_path).lower():
            return 'deployment'
        elif file_type == FileType.DOCUMENTATION:
            return 'documentation'
        
        return None
    
    def _calculate_quality_score(self, file_path: Path, file_type: FileType) -> float:
        """품질 점수 계산"""
        score = 0.5  # 기본 점수
        
        try:
            if file_type == FileType.SOURCE_CODE and file_path.exists():
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                # 문서화 체크
                if '"""' in content or '/*' in content or '//' in content:
                    score += 0.2
                
                # 테스트 관련 체크
                if any(keyword in content.lower() for keyword in ['test', 'assert', 'expect']):
                    score += 0.1
                
                # 에러 처리 체크
                if any(keyword in content.lower() for keyword in ['try', 'catch', 'except', 'error']):
                    score += 0.1
                
        except Exception:
            pass
        
        return min(1.0, score)
    
    def _calculate_complexity_score(self, file_path: Path, file_type: FileType) -> float:
        """복잡도 점수 계산"""
        if file_type != FileType.SOURCE_CODE or not file_path.exists():
            return 0.5
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 복잡도 지표 카운트
            complexity_keywords = self.detection_rules['quality_indicators']['complexity_keywords']
            complexity_count = sum(content.lower().count(keyword) for keyword in complexity_keywords)
            
            # 라인 수 기반 정규화
            line_count = len(content.split('\n'))
            if line_count > 0:
                complexity_ratio = complexity_count / line_count
                return min(1.0, complexity_ratio * 10)  # 스케일링
            
        except Exception:
            pass
        
        return 0.5
    
    def _calculate_maintainability_score(self, file_path: Path, file_type: FileType) -> float:
        """유지보수성 점수 계산"""
        if file_type != FileType.SOURCE_CODE or not file_path.exists():
            return 0.5
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            score = 0.5
            
            # 구조화 지표
            maintainability_keywords = self.detection_rules['quality_indicators']['maintainability_keywords']
            structure_count = sum(content.lower().count(keyword) for keyword in maintainability_keywords)
            
            if structure_count > 0:
                score += 0.2
            
            # 주석 비율
            comment_lines = len([line for line in content.split('\n') if line.strip().startswith(('#', '//', '/*'))])
            total_lines = len(content.split('\n'))
            
            if total_lines > 0:
                comment_ratio = comment_lines / total_lines
                score += min(0.3, comment_ratio * 2)
            
            return min(1.0, score)
            
        except Exception:
            pass
        
        return 0.5
    
    def _monitor_file_changes(self):
        """파일 변경 모니터링"""
        while self.scan_active:
            try:
                # 간단한 구현 - 실제로는 파일 시스템 이벤트 모니터링 사용 권장
                time.sleep(300)  # 5분마다 체크
                
                # 변경된 파일만 다시 스캔
                self._scan_modified_files()
                
            except Exception as e:
                print(f"파일 모니터링 오류: {str(e)}")
                time.sleep(60)
    
    def _scan_modified_files(self):
        """수정된 파일만 스캔"""
        # 최근 스캔 이후 수정된 파일들만 다시 분석
        pass  # 실제 구현에서는 파일 시스템 변경 감지 구현
    
    def _is_new_or_modified(self, metadata: FileMetadata) -> bool:
        """새 파일이거나 수정된 파일인지 확인"""
        with sqlite3.connect(self.metadata_db) as conn:
            cursor = conn.execute(
                "SELECT content_hash, modified_at FROM file_metadata WHERE file_path = ?",
                (metadata.file_path,)
            )
            row = cursor.fetchone()
            
            if not row:
                return True  # 새 파일
            
            # 해시나 수정 시간이 다르면 수정된 파일
            return (row[0] != metadata.content_hash or 
                   row[1] != metadata.modified_at.isoformat())
    
    def _save_file_metadata(self, metadata: FileMetadata):
        """파일 메타데이터 저장"""
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO file_metadata 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                metadata.file_path, metadata.file_name, metadata.file_type.value,
                metadata.file_status.value, metadata.size_bytes,
                metadata.created_at.isoformat(), metadata.modified_at.isoformat(),
                metadata.last_accessed.isoformat() if metadata.last_accessed else None,
                metadata.access_count, metadata.access_pattern.value,
                metadata.content_hash, metadata.mime_type, metadata.encoding,
                metadata.language, metadata.framework,
                json.dumps(metadata.dependencies), json.dumps(metadata.tags),
                metadata.purpose, metadata.role_ownership, metadata.project_phase,
                metadata.quality_score, metadata.complexity_score,
                metadata.maintainability_score,
                datetime.now().isoformat(), datetime.now().isoformat()
            ))
    
    def _get_all_tracked_files(self) -> List[str]:
        """추적 중인 모든 파일 목록"""
        with sqlite3.connect(self.metadata_db) as conn:
            cursor = conn.execute("SELECT file_path FROM file_metadata WHERE file_status != 'deleted'")
            return [row[0] for row in cursor.fetchall()]
    
    def _mark_file_deleted(self, file_path: str):
        """파일을 삭제됨으로 표시"""
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute(
                "UPDATE file_metadata SET file_status = 'deleted', updated_at = ? WHERE file_path = ?",
                (datetime.now().isoformat(), file_path)
            )
    
    def _analyze_file_relationships(self, current_files: set) -> int:
        """파일 간 관계 분석"""
        # 간단한 구현 - 실제로는 더 정교한 의존성 분석 필요
        relationships_found = 0
        
        # Python import 분석 예시
        for file_path in current_files:
            if file_path.endswith('.py'):
                try:
                    relationships = self._analyze_python_imports(file_path)
                    for relationship in relationships:
                        self._save_file_relationship(relationship)
                        relationships_found += 1
                except Exception:
                    pass
        
        return relationships_found
    
    def _analyze_python_imports(self, file_path: str) -> List[FileRelationship]:
        """Python import 분석"""
        relationships = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                
            # 간단한 import 패턴 매칭
            import_patterns = [
                r'from\s+\.([a-zA-Z_][a-zA-Z0-9_]*)\s+import',
                r'import\s+\.([a-zA-Z_][a-zA-Z0-9_]*)'
            ]
            
            for pattern in import_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    # 상대 경로로 파일 찾기
                    base_dir = Path(file_path).parent
                    imported_file = base_dir / f"{match}.py"
                    
                    if imported_file.exists():
                        relationship = FileRelationship(
                            from_file=file_path,
                            to_file=str(imported_file),
                            relationship_type="imports",
                            strength=0.8,
                            discovered_at=datetime.now()
                        )
                        relationships.append(relationship)
        
        except Exception:
            pass
        
        return relationships
    
    def _save_file_relationship(self, relationship: FileRelationship):
        """파일 관계 저장"""
        with sqlite3.connect(self.metadata_db) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO file_relationships 
                (from_file, to_file, relationship_type, strength, discovered_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                relationship.from_file, relationship.to_file,
                relationship.relationship_type, relationship.strength,
                relationship.discovered_at.isoformat()
            ))
    
    def _row_to_file_metadata(self, row: sqlite3.Row) -> FileMetadata:
        """데이터베이스 행을 FileMetadata로 변환"""
        return FileMetadata(
            file_path=row['file_path'],
            file_name=row['file_name'],
            file_type=FileType(row['file_type']),
            file_status=FileStatus(row['file_status']),
            size_bytes=row['size_bytes'],
            created_at=datetime.fromisoformat(row['created_at']),
            modified_at=datetime.fromisoformat(row['modified_at']),
            last_accessed=datetime.fromisoformat(row['last_accessed']) if row['last_accessed'] else None,
            access_count=row['access_count'],
            access_pattern=AccessPattern(row['access_pattern']),
            content_hash=row['content_hash'],
            mime_type=row['mime_type'],
            encoding=row['encoding'],
            language=row['language'],
            framework=row['framework'],
            dependencies=json.loads(row['dependencies']) if row['dependencies'] else [],
            tags=json.loads(row['tags']) if row['tags'] else [],
            purpose=row['purpose'],
            role_ownership=row['role_ownership'],
            project_phase=row['project_phase'],
            quality_score=row['quality_score'],
            complexity_score=row['complexity_score'],
            maintainability_score=row['maintainability_score']
        )
    
    def _content_matches_regex(self, file_path: str, regex_pattern: str) -> bool:
        """파일 콘텐츠가 정규식과 매치되는지 확인"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                return bool(re.search(regex_pattern, content, re.IGNORECASE))
        except Exception:
            return False
    
    def _extract_keywords_from_task(self, task: str) -> List[str]:
        """작업에서 키워드 추출"""
        # 간단한 키워드 추출
        words = re.findall(r'\b\w+\b', task.lower())
        
        # 불용어 제거
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return keywords[:10]
    
    def _calculate_file_relevance(self, task: str, file_metadata: FileMetadata) -> float:
        """파일 관련성 점수 계산"""
        score = 0.0
        
        task_keywords = set(self._extract_keywords_from_task(task))
        
        # 파일명 매칭
        file_keywords = set(re.findall(r'\b\w+\b', file_metadata.file_name.lower()))
        name_overlap = len(task_keywords & file_keywords)
        if name_overlap > 0:
            score += 0.4 * (name_overlap / len(task_keywords))
        
        # 태그 매칭
        tag_overlap = len(task_keywords & set(file_metadata.tags))
        if tag_overlap > 0:
            score += 0.3 * (tag_overlap / len(task_keywords))
        
        # 목적 매칭
        if file_metadata.purpose:
            purpose_keywords = set(re.findall(r'\b\w+\b', file_metadata.purpose.lower()))
            purpose_overlap = len(task_keywords & purpose_keywords)
            if purpose_overlap > 0:
                score += 0.2 * (purpose_overlap / len(task_keywords))
        
        # 품질 점수 가중치
        score *= file_metadata.quality_score
        
        return score
    
    def _update_access_pattern(self, file_path: str):
        """접근 패턴 업데이트"""
        with sqlite3.connect(self.metadata_db) as conn:
            # 최근 30일 접근 횟수 확인
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            
            cursor = conn.execute('''
                SELECT COUNT(*) FROM access_log 
                WHERE file_path = ? AND accessed_at >= ?
            ''', (file_path, thirty_days_ago))
            
            recent_access_count = cursor.fetchone()[0]
            
            # 접근 패턴 결정
            if recent_access_count >= 20:
                pattern = AccessPattern.FREQUENT
            elif recent_access_count >= 5:
                pattern = AccessPattern.OCCASIONAL
            elif recent_access_count >= 1:
                pattern = AccessPattern.RARE
            else:
                pattern = AccessPattern.NEVER_ACCESSED
            
            # 업데이트
            conn.execute('''
                UPDATE file_metadata 
                SET access_pattern = ? 
                WHERE file_path = ?
            ''', (pattern.value, file_path))

def main():
    """테스트 및 데모"""
    discovery_system = SmartFileDiscoverySystem("/home/jungh/workspace/multi_claude_code_sample")
    
    # 예시 1: 프로젝트 파일 스캔
    scan_results = discovery_system.scan_project_files(force_rescan=True)
    print(f"📁 스캔 결과: {scan_results['files_discovered']}개 파일 발견")
    
    # 예시 2: 파일 검색
    search_query = SearchQuery(
        keywords=['system', 'communication'],
        file_types=[FileType.SOURCE_CODE, FileType.DOCUMENTATION],
        quality_threshold=0.5,
        limit=5
    )
    
    search_results = discovery_system.smart_search(search_query)
    print(f"🔍 검색 결과: {len(search_results)}개 파일")
    for result in search_results[:3]:
        print(f"  - {result.file_name} (품질: {result.quality_score:.2f})")
    
    # 예시 3: 관련 파일 제안
    suggestions = discovery_system.suggest_relevant_files(
        role_id="business_analyst",
        current_task="사용자 인증 시스템 요구사항 분석",
        max_suggestions=5
    )
    
    print(f"💡 제안된 관련 파일 {len(suggestions)}개:")
    for file_metadata, relevance_score in suggestions:
        print(f"  - {file_metadata.file_name} (관련성: {relevance_score:.2f})")
    
    # 예시 4: 프로젝트 개요
    overview = discovery_system.get_project_file_overview()
    print("📊 프로젝트 파일 개요:")
    print(f"  - 총 파일 수: {overview['total_files']}")
    print(f"  - 평균 품질: {overview['quality_statistics']['average_quality']:.2f}")
    print(f"  - 타입 분포: {overview['type_distribution']}")

if __name__ == "__main__":
    main()