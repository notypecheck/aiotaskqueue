from sqlalchemy.orm import Mapped, mapped_column


class SqlalchemyResultTaskMixin:
    __tablename__ = "aiotaskqueue_result_task"

    key: Mapped[str] = mapped_column(primary_key=True)
    value: Mapped[str]
