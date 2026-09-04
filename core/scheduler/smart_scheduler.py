#!/usr/bin/env python3
"""
Gênesis Córtex - Sistema de Agendamento Inteligente
Lembretes contextuais, timers e agendamento avançado
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass, asdict
import json
from pathlib import Path

try:
    import schedule
    SCHEDULE_AVAILABLE = True
except ImportError:
    SCHEDULE_AVAILABLE = False


class ReminderType(Enum):
    """Tipos de lembrete"""
    ONE_TIME = "one_time"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CONTEXTUAL = "contextual"


class ReminderPriority(Enum):
    """Prioridade de lembrete"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class Reminder:
    """Representação de um lembrete"""
    id: str
    title: str
    description: str
    reminder_type: ReminderType
    priority: ReminderPriority
    due_time: Optional[datetime]
    recurring_interval: Optional[str]
    context_trigger: Optional[str]
    completed: bool
    created_at: datetime
    notified: bool
    voice_enabled: bool


@dataclass
class Timer:
    """Representação de um timer"""
    id: str
    name: str
    duration_seconds: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    completed: bool
    paused: bool
    paused_duration: int
    voice_enabled: bool


class SmartScheduler:
    """Sistema de agendamento inteligente"""
    
    def __init__(self, config: Dict[str, Any]):
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.scheduler_config = config.get("scheduler", {})
        
        # Estado
        self.reminders: Dict[str, Reminder] = {}
        self.timers: Dict[str, Timer] = {}
        self.active_timers: Dict[str, asyncio.Task] = {}
        
        # Arquivo de persistência
        self.storage_path = Path("data/scheduler.json")
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Configurações
        self.voice_enabled = self.scheduler_config.get("voice_enabled", True)
        self.default_reminder_sound = self.scheduler_config.get("default_sound", "bell")
        
        # Contexto atual
        self.current_context: Dict[str, Any] = {}
        
        # Inicializar
        self._load_reminders()
        
        if SCHEDULE_AVAILABLE:
            self._setup_schedule()
    
    async def initialize(self) -> None:
        """Inicializa o scheduler"""
        self.logger.info("Inicializando sistema de agendamento inteligente")
        
        # Iniciar verificação de lembretes
        asyncio.create_task(self._check_reminders_loop())
        
        # Iniciar timers ativos
        await self._restore_active_timers()
        
        self.logger.info("Sistema de agendamento inicializado")
    
    def _setup_schedule(self) -> None:
        """Configura o scheduler para tarefas recorrentes"""
        schedule.every(1).minutes.do(self._check_due_reminders)
        schedule.every(1).hours.do(self._cleanup_completed_reminders)
        schedule.every().day.at("00:00").do(self._daily_cleanup)
    
    def _load_reminders(self) -> None:
        """Carrega lembretes do arquivo de persistência"""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for reminder_data in data.get("reminders", []):
                    reminder = Reminder(
                        id=reminder_data["id"],
                        title=reminder_data["title"],
                        description=reminder_data["description"],
                        reminder_type=ReminderType(reminder_data["reminder_type"]),
                        priority=ReminderPriority(reminder_data["priority"]),
                        due_time=datetime.fromisoformat(reminder_data["due_time"]) if reminder_data.get("due_time") else None,
                        recurring_interval=reminder_data.get("recurring_interval"),
                        context_trigger=reminder_data.get("context_trigger"),
                        completed=reminder_data["completed"],
                        created_at=datetime.fromisoformat(reminder_data["created_at"]),
                        notified=reminder_data["notified"],
                        voice_enabled=reminder_data["voice_enabled"]
                    )
                    self.reminders[reminder.id] = reminder
                
                self.logger.info(f"Carregados {len(self.reminders)} lembretes")
                
            except Exception as e:
                self.logger.error(f"Erro ao carregar lembretes: {e}")
    
    def _save_reminders(self) -> None:
        """Salva lembretes no arquivo de persistência"""
        try:
            data = {
                "reminders": [asdict(r) for r in self.reminders.values()],
                "timers": [asdict(t) for t in self.timers.values()]
            }
            
            # Converter datetime para string
            def datetime_handler(obj):
                if isinstance(obj, datetime):
                    return obj.isoformat()
                raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
            
            with open(self.storage_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, default=datetime_handler, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Erro ao salvar lembretes: {e}")
    
    async def create_reminder(
        self,
        title: str,
        description: str,
        due_time: Optional[datetime] = None,
        reminder_type: ReminderType = ReminderType.ONE_TIME,
        priority: ReminderPriority = ReminderPriority.MEDIUM,
        recurring_interval: Optional[str] = None,
        context_trigger: Optional[str] = None,
        voice_enabled: bool = True
    ) -> str:
        """Cria um novo lembrete"""
        import uuid
        
        reminder_id = str(uuid.uuid4())
        
        reminder = Reminder(
            id=reminder_id,
            title=title,
            description=description,
            reminder_type=reminder_type,
            priority=priority,
            due_time=due_time,
            recurring_interval=recurring_interval,
            context_trigger=context_trigger,
            completed=False,
            created_at=datetime.now(),
            notified=False,
            voice_enabled=voice_enabled
        )
        
        self.reminders[reminder_id] = reminder
        self._save_reminders()
        
        self.logger.info(f"Lembrete criado: {title} ({reminder_id})")
        
        return reminder_id
    
    async def create_timer(
        self,
        name: str,
        duration_seconds: int,
        voice_enabled: bool = True
    ) -> str:
        """Cria um novo timer"""
        import uuid
        
        timer_id = str(uuid.uuid4())
        
        timer = Timer(
            id=timer_id,
            name=name,
            duration_seconds=duration_seconds,
            start_time=None,
            end_time=None,
            completed=False,
            paused=False,
            paused_duration=0,
            voice_enabled=voice_enabled
        )
        
        self.timers[timer_id] = timer
        self._save_reminders()
        
        self.logger.info(f"Timer criado: {name} ({duration_seconds}s)")
        
        return timer_id
    
    async def start_timer(self, timer_id: str) -> bool:
        """Inicia um timer"""
        if timer_id not in self.timers:
            return False
        
        timer = self.timers[timer_id]
        
        if timer.start_time and not timer.paused:
            return False  # Já está rodando
        
        timer.start_time = datetime.now()
        timer.end_time = timer.start_time + timedelta(seconds=timer.duration_seconds - timer.paused_duration)
        timer.paused = False
        
        # Criar tarefa assíncrona para o timer
        task = asyncio.create_task(self._run_timer(timer_id))
        self.active_timers[timer_id] = task
        
        self._save_reminders()
        
        self.logger.info(f"Timer iniciado: {timer.name}")
        
        return True
    
    async def _run_timer(self, timer_id: str) -> None:
        """Executa um timer em background"""
        timer = self.timers[timer_id]
        
        try:
            while not timer.completed and not timer.paused:
                if timer.end_time and datetime.now() >= timer.end_time:
                    await self._complete_timer(timer_id)
                    break
                
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            self.logger.info(f"Timer cancelado: {timer.name}")
        except Exception as e:
            self.logger.error(f"Erro no timer {timer_id}: {e}")
    
    async def pause_timer(self, timer_id: str) -> bool:
        """Pausa um timer"""
        if timer_id not in self.timers:
            return False
        
        timer = self.timers[timer_id]
        
        if not timer.start_time or timer.paused:
            return False
        
        timer.paused = True
        timer.paused_duration += (datetime.now() - timer.start_time).total_seconds()
        
        # Cancelar tarefa ativa
        if timer_id in self.active_timers:
            self.active_timers[timer_id].cancel()
            del self.active_timers[timer_id]
        
        self._save_reminders()
        
        self.logger.info(f"Timer pausado: {timer.name}")
        
        return True
    
    async def resume_timer(self, timer_id: str) -> bool:
        """Retoma um timer pausado"""
        if timer_id not in self.timers:
            return False
        
        timer = self.timers[timer_id]
        
        if not timer.paused:
            return False
        
        return await self.start_timer(timer_id)
    
    async def cancel_timer(self, timer_id: str) -> bool:
        """Cancela um timer"""
        if timer_id not in self.timers:
            return False
        
        timer = self.timers[timer_id]
        
        # Cancelar tarefa ativa
        if timer_id in self.active_timers:
            self.active_timers[timer_id].cancel()
            del self.active_timers[timer_id]
        
        del self.timers[timer_id]
        self._save_reminders()
        
        self.logger.info(f"Timer cancelado: {timer.name}")
        
        return True
    
    async def _complete_timer(self, timer_id: str) -> None:
        """Marca timer como completo"""
        if timer_id not in self.timers:
            return
        
        timer = self.timers[timer_id]
        timer.completed = True
        timer.end_time = datetime.now()
        
        # Notificar
        await self._notify_timer_complete(timer)
        
        # Remover de timers ativos
        if timer_id in self.active_timers:
            del self.active_timers[timer_id]
        
        self._save_reminders()
    
    async def _notify_timer_complete(self, timer: Timer) -> None:
        """Notifica conclusão de timer"""
        message = f"Timer '{timer.name}' concluído!"
        
        self.logger.info(message)
        
        # Reproduzir som/voz se habilitado
        if timer.voice_enabled:
            await self._play_notification_sound()
            # Aqui poderia integrar com o sistema de voz
    
    async def _play_notification_sound(self) -> None:
        """Reproduz som de notificação"""
        try:
            # Usar beep do sistema ou arquivo de som
            import subprocess
            subprocess.run(["paplay", "/usr/share/sounds/freedesktop/stereo/complete.oga"], 
                         capture_output=True, timeout=5)
        except Exception:
            # Fallback para beep do terminal
            print('\a')
    
    async def _restore_active_timers(self) -> None:
        """Restaura timers que estavam ativos"""
        for timer_id, timer in self.timers.items():
            if timer.start_time and not timer.completed and not timer.paused:
                # Recalcular tempo restante
                if timer.end_time and datetime.now() < timer.end_time:
                    await self.start_timer(timer_id)
                else:
                    # Timer já expirou enquanto estava desligado
                    await self._complete_timer(timer_id)
    
    async def _check_reminders_loop(self) -> None:
        """Loop contínuo de verificação de lembretes"""
        while True:
            await self._check_due_reminders()
            await asyncio.sleep(60)  # Verificar a cada minuto
    
    def _check_due_reminders(self) -> None:
        """Verifica lembretes que estão vencendo"""
        now = datetime.now()
        
        for reminder_id, reminder in self.reminders.items():
            if reminder.completed or reminder.notified:
                continue
            
            # Verificar lembretes por tempo
            if reminder.due_time and now >= reminder.due_time:
                asyncio.create_task(self._notify_reminder(reminder_id))
            
            # Verificar lembretes contextuais
            if reminder.reminder_type == ReminderType.CONTEXTUAL and reminder.context_trigger:
                if self._check_context_trigger(reminder.context_trigger):
                    asyncio.create_task(self._notify_reminder(reminder_id))
    
    def _check_context_trigger(self, trigger: str) -> bool:
        """Verifica se trigger contextual foi ativado"""
        # Implementar lógica contextual
        # Ex: trigger "coding_start" quando usuário começa a programar
        return trigger in self.current_context.get("active_triggers", [])
    
    async def _notify_reminder(self, reminder_id: str) -> None:
        """Notifica um lembrete"""
        if reminder_id not in self.reminders:
            return
        
        reminder = self.reminders[reminder_id]
        reminder.notified = True
        
        message = f"Lembrete: {reminder.title}"
        if reminder.description:
            message += f" - {reminder.description}"
        
        self.logger.info(message)
        
        # Reproduzir notificação
        if reminder.voice_enabled:
            await self._play_notification_sound()
            # Aqui poderia usar o sistema de voz para falar o lembrete
        
        # Se for recorrente, criar próximo lembrete
        if reminder.recurring_interval:
            await self._schedule_next_reminder(reminder)
        
        self._save_reminders()
    
    async def _schedule_next_reminder(self, reminder: Reminder) -> None:
        """Agenda próxima ocorrência de lembrete recorrente"""
        if not reminder.due_time:
            return
        
        next_due = self._calculate_next_due_time(reminder.due_time, reminder.recurring_interval)
        
        if next_due:
            await self.create_reminder(
                title=reminder.title,
                description=reminder.description,
                due_time=next_due,
                reminder_type=reminder.reminder_type,
                priority=reminder.priority,
                recurring_interval=reminder.recurring_interval,
                context_trigger=reminder.context_trigger,
                voice_enabled=reminder.voice_enabled
            )
    
    def _calculate_next_due_time(self, due_time: datetime, interval: str) -> Optional[datetime]:
        """Calcula próxima data de vencimento baseado no intervalo"""
        if interval == "daily":
            return due_time + timedelta(days=1)
        elif interval == "weekly":
            return due_time + timedelta(weeks=1)
        elif interval == "monthly":
            # Aproximação simples para mensal
            return due_time + timedelta(days=30)
        
        return None
    
    async def complete_reminder(self, reminder_id: str) -> bool:
        """Marca lembrete como completo"""
        if reminder_id not in self.reminders:
            return False
        
        reminder = self.reminders[reminder_id]
        reminder.completed = True
        
        self._save_reminders()
        
        self.logger.info(f"Lembrete completado: {reminder.title}")
        
        return True
    
    async def delete_reminder(self, reminder_id: str) -> bool:
        """Deleta um lembrete"""
        if reminder_id not in self.reminders:
            return False
        
        del self.reminders[reminder_id]
        self._save_reminders()
        
        self.logger.info(f"Lembrete deletado: {reminder_id}")
        
        return True
    
    def update_context(self, context: Dict[str, Any]) -> None:
        """Atualiza contexto atual"""
        self.current_context.update(context)
        
        # Verificar lembretes contextuais
        asyncio.create_task(self._check_contextual_reminders())
    
    async def _check_contextual_reminders(self) -> None:
        """Verifica lembretes contextuais baseados no contexto atual"""
        for reminder_id, reminder in self.reminders.items():
            if (reminder.reminder_type == ReminderType.CONTEXTUAL and 
                reminder.context_trigger and 
                not reminder.completed and 
                not reminder.notified):
                
                if self._check_context_trigger(reminder.context_trigger):
                    await self._notify_reminder(reminder_id)
    
    def get_reminders(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        """Retorna lista de lembretes"""
        reminders = []
        
        for reminder in self.reminders.values():
            if not include_completed and reminder.completed:
                continue
            
            reminders.append({
                "id": reminder.id,
                "title": reminder.title,
                "description": reminder.description,
                "type": reminder.reminder_type.value,
                "priority": reminder.priority.value,
                "due_time": reminder.due_time.isoformat() if reminder.due_time else None,
                "completed": reminder.completed,
                "notified": reminder.notified
            })
        
        return sorted(reminders, key=lambda x: x.get("due_time") or "")
    
    def get_timers(self) -> List[Dict[str, Any]]:
        """Retorna lista de timers"""
        timers = []
        
        for timer in self.timers.values():
            remaining = 0
            if timer.start_time and timer.end_time and not timer.completed:
                remaining = max(0, (timer.end_time - datetime.now()).total_seconds())
            
            timers.append({
                "id": timer.id,
                "name": timer.name,
                "duration": timer.duration_seconds,
                "remaining": int(remaining),
                "completed": timer.completed,
                "paused": timer.paused
            })
        
        return timers
    
    def _cleanup_completed_reminders(self) -> None:
        """Limpa lembretes completados antigos"""
        cutoff = datetime.now() - timedelta(days=7)
        
        to_delete = [
            reminder_id for reminder_id, reminder in self.reminders.items()
            if reminder.completed and reminder.created_at < cutoff
        ]
        
        for reminder_id in to_delete:
            del self.reminders[reminder_id]
        
        if to_delete:
            self._save_reminders()
            self.logger.info(f"Limpos {len(to_delete)} lembretes completados antigos")
    
    def _daily_cleanup(self) -> None:
        """Limpeza diária"""
        self._cleanup_completed_reminders()
        
        # Limpar timers completos
        completed_timers = [
            timer_id for timer_id, timer in self.timers.items()
            if timer.completed
        ]
        
        for timer_id in completed_timers:
            del self.timers[timer_id]
        
        if completed_timers:
            self._save_reminders()
            self.logger.info(f"Limpos {len(completed_timers)} timers completos")
    
    async def cleanup(self) -> None:
        """Limpa recursos do scheduler"""
        # Cancelar todos os timers ativos
        for timer_id, task in self.active_timers.items():
            task.cancel()
        
        self.active_timers.clear()
        
        self.logger.info("Scheduler finalizado")