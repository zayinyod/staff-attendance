from django.db import models

class CodeMaster(models.Model):
    code_type = models.CharField(max_length=50)
    code = models.CharField(max_length=20)
    description = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("code_type", "code")

    def __str__(self):
        return f"[{self.code_type}: {self.code}] {self.description}"
