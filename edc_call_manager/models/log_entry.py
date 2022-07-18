from django.db import models
from django.db.models import PROTECT
from edc_model.models import BaseUuidModel, HistoricalRecords

from ..model_mixins import LogEntryModelMixin
from .log import Log


class LogEntry(LogEntryModelMixin, BaseUuidModel):

    log = models.ForeignKey(Log, on_delete=PROTECT)

    history = HistoricalRecords()

    @property
    def subject_identifier(self):
        return self.log.call.subject_identifier

    class Meta(LogEntryModelMixin.Meta):
        verbose_name = "Log Entry"
        verbose_name_plural = "Log Entries"
