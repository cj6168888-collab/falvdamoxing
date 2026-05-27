"""
案件权限系统 - JWT鉴权 + 团队协作共享（biz-11）
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from functools import wraps
import hashlib
import secrets

try:
    import jwt
    JWT_AVAILABLE = True
except ImportError:
    JWT_AVAILABLE = False


class UserRole(str, Enum):
    """用户角色"""
    ADMIN = "admin"          # 管理员
    LAWYER = "lawyer"        # 律师
    ASSISTANT = "assistant"  # 助理
    CLIENT = "client"         # 客户
    VIEWER = "viewer"         # 查看者


class Permission(str, Enum):
    """权限类型"""
    CASE_READ = "case_read"          # 查看案件
    CASE_EDIT = "case_edit"         # 编辑案件
    CASE_DELETE = "case_delete"     # 删除案件
    EVIDENCE_UPLOAD = "evidence_upload"  # 上传证据
    EVIDENCE_DELETE = "evidence_delete"   # 删除证据
    DOCUMENT_GENERATE = "document_generate"  # 生成文书
    DOCUMENT_EXPORT = "document_export"     # 导出文书
    DEADLINE_MANAGE = "deadline_manage"   # 管理期限
    TEAM_MANAGE = "team_manage"           # 管理团队
    SETTINGS = "settings"                  # 系统设置


@dataclass
class User:
    """用户"""
    user_id: str
    username: str
    email: Optional[str]
    role: UserRole
    team_id: Optional[str] = None
    created_at: datetime = None
    last_login: datetime = None
    
    def to_dict(self) -> Dict:
        result = asdict(self)
        result['role'] = self.role.value if isinstance(self.role, Enum) else self.role
        return result


@dataclass
class CasePermission:
    """案件权限"""
    case_id: int
    user_id: str
    permissions: List[str]  # Permission枚举值列表
    granted_by: str  # 授权人
    granted_at: datetime
    expires_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        if self.expires_at and datetime.now() > self.expires_at:
            return False
        return True


@dataclass
class Team:
    """团队"""
    team_id: str
    name: str
    owner_id: str  # 团队所有者
    description: Optional[str] = None
    members: List[str] = None  # 用户ID列表
    created_at: datetime = None
    
    def __post_init__(self):
        if self.members is None:
            self.members = []


class JWTAuthService:
    """
    JWT鉴权服务（biz-11）
    
    提供：
    1. 用户注册/登录
    2. JWT Token生成与验证
    3. 案件权限管理
    4. 团队协作共享
    """
    
    # 角色默认权限
    ROLE_PERMISSIONS = {
        UserRole.ADMIN: [p.value for p in Permission],
        UserRole.LAWYER: [
            Permission.CASE_READ.value, Permission.CASE_EDIT.value,
            Permission.EVIDENCE_UPLOAD.value, Permission.EVIDENCE_DELETE.value,
            Permission.DOCUMENT_GENERATE.value, Permission.DOCUMENT_EXPORT.value,
            Permission.DEADLINE_MANAGE.value, Permission.TEAM_MANAGE.value
        ],
        UserRole.ASSISTANT: [
            Permission.CASE_READ.value, Permission.CASE_EDIT.value,
            Permission.EVIDENCE_UPLOAD.value, Permission.DOCUMENT_GENERATE.value
        ],
        UserRole.CLIENT: [
            Permission.CASE_READ.value, Permission.EVIDENCE_UPLOAD.value
        ],
        UserRole.VIEWER: [
            Permission.CASE_READ.value
        ]
    }
    
    def __init__(self, secret_key: Optional[str] = None):
        """
        初始化JWT服务
        
        Args:
            secret_key: JWT签名密钥，默认自动生成
        """
        if secret_key is None:
            secret_key = secrets.token_urlsafe(32)
        
        self.secret_key = secret_key
        self.algorithm = "HS256"
        self.token_expiry = timedelta(days=7)  # Token 7天有效期
        self.refresh_expiry = timedelta(days=30)  # Refresh Token 30天
        
        # 内存存储（生产环境应使用数据库）
        self._users: Dict[str, User] = {}
        self._case_permissions: Dict[int, Dict[str, CasePermission]] = {}
        self._teams: Dict[str, Team] = {}
        self._api_keys: Dict[str, str] = {}  # API Key -> User ID
    
    def register_user(
        self,
        username: str,
        password: str,
        email: Optional[str] = None,
        role: UserRole = UserRole.CLIENT
    ) -> Dict:
        """
        注册用户
        
        Args:
            username: 用户名
            password: 密码（会进行哈希）
            email: 邮箱
            role: 角色
            
        Returns:
            用户信息（不含密码）
        """
        # 检查用户名是否存在
        if any(u.username == username for u in self._users.values()):
            return {"success": False, "error": "用户名已存在"}
        
        user_id = secrets.token_urlsafe(16)
        
        # 密码哈希
        password_hash = self._hash_password(password)
        
        user = User(
            user_id=user_id,
            username=username,
            email=email,
            role=role,
            created_at=datetime.now()
        )
        
        # 存储（密码哈希单独存储）
        self._users[user_id] = user
        self._users[f"_pwd_{username}"] = password_hash  # 简化存储
        
        return {"success": True, "user": user.to_dict()}
    
    def authenticate(
        self,
        username: str,
        password: str
    ) -> Optional[Dict]:
        """
        用户认证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            Token信息或None
        """
        # 验证密码
        stored_hash = self._users.get(f"_pwd_{username}")
        if not stored_hash or not self._verify_password(password, stored_hash):
            return None
        
        # 查找用户
        user = next((u for u in self._users.values() if u.username == username), None)
        if not user:
            return None
        
        # 生成Token
        tokens = self._generate_tokens(user)
        
        # 更新登录时间
        user.last_login = datetime.now()
        
        return {
            "success": True,
            "tokens": tokens,
            "user": user.to_dict()
        }
    
    def create_api_key(self, user_id: str) -> Dict:
        """
        创建API Key（用于程序化访问）
        
        Args:
            user_id: 用户ID
            
        Returns:
            API Key信息
        """
        if user_id not in self._users:
            return {"success": False, "error": "用户不存在"}
        
        api_key = f"lklm_{secrets.token_urlsafe(32)}"
        api_secret_hash = self._hash_password(secrets.token_urlsafe(32))
        
        self._api_keys[api_key] = user_id
        self._users[f"_apikey_{api_key}"] = api_secret_hash
        
        return {
            "success": True,
            "api_key": api_key,
            "api_secret_hash": api_secret_hash,
            "user_id": user_id
        }
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证Token
        
        Args:
            token: JWT Token
            
        Returns:
            用户信息或None
        """
        if not JWT_AVAILABLE:
            return None
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("user_id")
            
            if user_id not in self._users:
                return None
            
            user = self._users[user_id]
            return {"user": user.to_dict(), "payload": payload}
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict]:
        """
        刷新Token
        
        Args:
            refresh_token: Refresh Token
            
        Returns:
            新的Token信息或None
        """
        if not JWT_AVAILABLE:
            return None
        
        try:
            payload = jwt.decode(
                refresh_token, 
                self.secret_key, 
                algorithms=[self.algorithm]
            )
            
            if payload.get("type") != "refresh":
                return None
            
            user_id = payload.get("user_id")
            if user_id not in self._users:
                return None
            
            user = self._users[user_id]
            tokens = self._generate_tokens(user)
            
            return {"success": True, "tokens": tokens}
        except Exception:
            return None
    
    def grant_case_permission(
        self,
        case_id: int,
        user_id: str,
        permissions: List[str],
        granted_by: str,
        expires_at: Optional[datetime] = None
    ) -> bool:
        """
        授予案件权限
        
        Args:
            case_id: 案件ID
            user_id: 被授权用户ID
            permissions: 权限列表
            granted_by: 授权人ID
            expires_at: 过期时间
            
        Returns:
            是否成功
        """
        if case_id not in self._case_permissions:
            self._case_permissions[case_id] = {}
        
        self._case_permissions[case_id][user_id] = CasePermission(
            case_id=case_id,
            user_id=user_id,
            permissions=permissions,
            granted_by=granted_by,
            granted_at=datetime.now(),
            expires_at=expires_at
        )
        
        return True
    
    def check_case_permission(
        self,
        case_id: int,
        user_id: str,
        permission: str
    ) -> bool:
        """
        检查案件权限
        
        Args:
            case_id: 案件ID
            user_id: 用户ID
            permission: 权限类型
            
        Returns:
            是否有权限
        """
        # 管理员拥有所有权限
        user = self._users.get(user_id)
        if user and user.role == UserRole.ADMIN:
            return True
        
        # 检查案件权限
        if case_id in self._case_permissions:
            case_perm = self._case_permissions[case_id].get(user_id)
            if case_perm and case_perm.is_valid() and permission in case_perm.permissions:
                return True
        
        return False
    
    def create_team(
        self,
        name: str,
        owner_id: str,
        description: Optional[str] = None
    ) -> Dict:
        """
        创建团队
        
        Args:
            name: 团队名称
            owner_id: 所有者ID
            description: 描述
            
        Returns:
            团队信息
        """
        team_id = secrets.token_urlsafe(16)
        
        team = Team(
            team_id=team_id,
            name=name,
            owner_id=owner_id,
            description=description,
            created_at=datetime.now()
        )
        team.members = [owner_id]  # 所有者自动加入
        
        self._teams[team_id] = team
        
        # 更新用户团队信息
        if owner_id in self._users:
            self._users[owner_id].team_id = team_id
        
        return {"success": True, "team_id": team_id}
    
    def invite_team_member(
        self,
        team_id: str,
        invited_user_id: str,
        inviter_id: str
    ) -> bool:
        """
        邀请团队成员
        
        Args:
            team_id: 团队ID
            invited_user_id: 被邀请用户ID
            inviter_id: 邀请人ID
            
        Returns:
            是否成功
        """
        if team_id not in self._teams:
            return False
        
        team = self._teams[team_id]
        
        # 只有所有者或管理员可以邀请
        if inviter_id != team.owner_id:
            return False
        
        if invited_user_id not in team.members:
            team.members.append(invited_user_id)
        
        # 更新用户团队信息
        if invited_user_id in self._users:
            self._users[invited_user_id].team_id = team_id
        
        return True
    
    def _generate_tokens(self, user: User) -> Dict:
        """生成Access Token和Refresh Token"""
        now = datetime.now()
        
        # Access Token
        access_payload = {
            "user_id": user.user_id,
            "username": user.username,
            "role": user.role.value if isinstance(user.role, Enum) else user.role,
            "type": "access",
            "exp": now + self.token_expiry,
            "iat": now
        }
        
        access_token = jwt.encode(access_payload, self.secret_key, algorithm=self.algorithm)
        
        # Refresh Token
        refresh_payload = {
            "user_id": user.user_id,
            "type": "refresh",
            "exp": now + self.refresh_expiry,
            "iat": now
        }
        
        refresh_token = jwt.encode(refresh_payload, self.secret_key, algorithm=self.algorithm)
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "expires_in": int(self.token_expiry.total_seconds())
        }
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """密码哈希"""
        salt = secrets.token_hex(16)
        pwd_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt.encode('utf-8'),
            100000
        )
        return salt + pwd_hash.hex()
    
    @staticmethod
    def _verify_password(password: str, stored_hash: str) -> bool:
        """验证密码"""
        try:
            salt = stored_hash[:32]
            stored_pwd_hash = stored_hash[32:]
            pwd_hash = hashlib.pbkdf2_hmac(
                'sha256',
                password.encode('utf-8'),
                salt.encode('utf-8'),
                100000
            )
            return pwd_hash.hex() == stored_pwd_hash
        except Exception:
            return False


# 全局实例
jwt_auth_service = JWTAuthService()
