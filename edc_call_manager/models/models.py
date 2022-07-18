from django.db import models
from django.db.models import PROTECT
from edc_model.models import BaseUuidModel, HistoricalRecords

from .model_mixins import CallModelMixin, LogEntryModelMixin, LogModelMixin


class Call(CallModelMixin, BaseUuidModel):

    history = HistoricalRecords()

    class Meta(CallModelMixin.Meta):
        verbose_name = "Call"
        verbose_name_plural = "Calls"


class Log(LogModelMixin, BaseUuidModel):

    call = models.ForeignKey(Call, on_delete=PROTECT)

    history = HistoricalRecords()

    class Meta(LogModelMixin.Meta):
        verbose_name = "Log"
        verbose_name_plural = "Logs"


class LogEntry(LogEntryModelMixin, BaseUuidModel):

    log = models.ForeignKey(Log, on_delete=PROTECT)

    history = HistoricalRecords()

    class Meta(LogEntryModelMixin.Meta):
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"
