from django.db import models
from django.db.models import PROTECT
from edc_model.models import BaseUuidModel, HistoricalRecords

from ..model_mixins import LogModelMixin
from .call import Call


class Log(LogModelMixin, BaseUuidModel):

    call = models.ForeignKey(Call, on_delete=PROTECT)

    history = HistoricalRecords()

    @property
    def subject_identifier(self):
        return self.call.subject_identifier

    class Meta(LogModelMixin.Meta):
        verbose_name = "Log"
        verbose_name_plural = "Logs"
