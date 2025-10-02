# backend/app/models/model_selection.py

from sqlalchemy import Column, String, JSON, DateTime, Boolean, Text
from sqlalchemy.orm.attributes import flag_modified
from datetime import datetime, timedelta
from typing import Optional, List, Dict
from app.database import Base

class ModelSelection(Base):
    """Speichert ausgewählte Models pro Provider"""
    __tablename__ = "model_selection"
    
    provider = Column(String, primary_key=True)
    available_models = Column(JSON, default=dict)  # {model_id: {name, description, enabled}}
    last_fetched = Column(DateTime, default=datetime.utcnow)
    
    @classmethod
    def get_enabled_models(cls, db, provider: str) -> List[str]:
        """Gibt nur aktivierte Models zurück für Chat-Page"""
        selection = db.query(cls).filter(cls.provider == provider).first()
        
        if not selection or not selection.available_models:
            return []
        
        # Return nur die Models wo enabled=True
        enabled = []
        for model_id, info in selection.available_models.items():
            if info.get('enabled', False):
                enabled.append(model_id)
        
        return enabled
    
    @classmethod
    def get_all_models(cls, db, provider: str) -> Dict:
        """Gibt alle verfügbaren Models zurück für Config-Page"""
        selection = db.query(cls).filter(cls.provider == provider).first()
        
        if not selection:
            return {}
            
        return selection.available_models or {}
    
    @classmethod
    def needs_refresh(cls, db, provider: str) -> bool:
        """Prüft ob Model-Liste älter als 1 Woche ist"""
        selection = db.query(cls).filter(cls.provider == provider).first()
        
        if not selection:
            return True
            
        age = datetime.utcnow() - selection.last_fetched
        return age > timedelta(weeks=1)
    
    @classmethod
    def update_available_models(cls, db, provider: str, models: List[Dict]):
        """
        Aktualisiert verfügbare Models von Provider
        models = [{"id": "model-name", "description": "..."}]
        """
        selection = db.query(cls).filter(cls.provider == provider).first()
        
        if not selection:
            selection = cls(provider=provider)
            db.add(selection)
        
        # Merge neue Models mit bestehender Auswahl
        current = selection.available_models or {}
        updated = {}
        
        for model in models:
            model_id = model['id']
            # Behalte enabled-Status wenn Model schon existiert
            was_enabled = current.get(model_id, {}).get('enabled', False)
            updated[model_id] = {
                'name': model.get('name', model_id),
                'description': model.get('description', ''),
                'enabled': was_enabled
            }
        
        selection.available_models = updated
        selection.last_fetched = datetime.utcnow()
        flag_modified(selection, "available_models")
        db.commit()
        
        return selection
    
    @classmethod  
    def toggle_model(cls, db, provider: str, model_id: str, enabled: bool):
        """Aktiviert/Deaktiviert ein Model"""
        selection = db.query(cls).filter(cls.provider == provider).first()
        
        if selection and selection.available_models:
            if model_id in selection.available_models:
                selection.available_models[model_id]['enabled'] = enabled
                flag_modified(selection, "available_models")
                db.commit()
                return True
        
        return False
    
    @classmethod
    def bulk_update_selection(cls, db, provider: str, enabled_models: List[str]):
        """Bulk-Update der Model-Auswahl"""
        selection = db.query(cls).filter(cls.provider == provider).first()
        
        if selection and selection.available_models:
            # Alle auf disabled setzen
            for model_id in selection.available_models:
                selection.available_models[model_id]['enabled'] = False
            
            # Ausgewählte aktivieren
            for model_id in enabled_models:
                if model_id in selection.available_models:
                    selection.available_models[model_id]['enabled'] = True
            
            # KRITISCH: SQLAlchemy mitteilen dass sich JSON geändert hat
            flag_modified(selection, "available_models")
            db.commit()
            return True
        
        return False