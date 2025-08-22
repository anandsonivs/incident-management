from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.crud.base import CRUDBase
from app.models.team import Team
from app.schemas.team import TeamCreate, TeamUpdate

class CRUDTeam(CRUDBase[Team, TeamCreate, TeamUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Optional[Team]:
        return db.query(Team).filter(Team.name == name).first()
    
    def get_active_teams(self, db: Session) -> List[Team]:
        return db.query(Team).filter(Team.is_active == True).all()
    
    def get_team_with_user_count(self, db: Session, *, team_id: int) -> Optional[Team]:
        """Get team with user count."""
        from app.models.user import User
        result = db.query(
            Team,
            func.count(User.id).label('user_count')
        ).outerjoin(User).filter(Team.id == team_id).group_by(Team.id).first()
        
        if result:
            team, user_count = result
            team.user_count = user_count
            return team
        return None
    
    def get_all_teams_with_user_count(self, db: Session, *, skip: int = 0, limit: int = 100) -> List[dict]:
        """Get all teams with user count."""
        from app.models.user import User
        result = db.query(
            Team,
            func.count(User.id).label('user_count')
        ).outerjoin(User).group_by(Team.id).offset(skip).limit(limit).all()
        
        teams = []
        for team, user_count in result:
            team_dict = {
                'id': team.id,
                'name': team.name,
                'description': team.description,
                'is_active': team.is_active,
                'created_at': team.created_at,
                'updated_at': team.updated_at,
                'user_count': user_count
            }
            teams.append(team_dict)
        
        return teams

team = CRUDTeam(Team)
