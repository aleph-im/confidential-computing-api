from enum import Enum
from typing import Optional

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy.orm import relationship, Session, selectinload
from sqlalchemy_utils.types import ChoiceType

from .db import Base


class VmState(str, Enum):
    # The VM was created but not yet started
    STOPPED = "stopped"
    # The VM was created in Qemu but still needs to go through the SEV launch process
    STARTED = "started"
    # The VM is running and can be used by the user
    RUNNING = "running"


class Vm(Base):
    __tablename__ = "vms"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(String, primary_key=True)
    owner = Column(String, nullable=False)
    state = Column(ChoiceType(VmState), nullable=False)
    image_id = Column(ForeignKey("vm_images.id"), nullable=True)
    number_of_cores = Column(Integer, nullable=False)
    memory = Column(Integer, nullable=False)
    sev_policy = Column(Integer, nullable=True)
    ssh_port = Column(Integer, nullable=True)
    qmp_port = Column(Integer, nullable=True)
    pid = Column(Integer, nullable=True)
    creation_datetime = Column(DateTime, nullable=False, server_default=func.now())

    image = relationship("VmImage", back_populates="vm", uselist=False)


class VmImage(Base):
    __tablename__ = "vm_images"
    __mapper_args__ = {"eager_defaults": True}

    id = Column(String, primary_key=True)
    filename = Column(String, nullable=False)
    upload_datetime = Column(DateTime, nullable=False, server_default=func.now())

    vm = relationship(Vm, back_populates="image")


async def fetch_vm(session: Session, vm_id: str) -> Optional[Vm]:
    select_stmt = select(Vm).where(Vm.id == vm_id).options(selectinload(Vm.image))
    vms = (await session.execute(select_stmt)).one_or_none()

    return vms[0] if vms is not None else None
