from tortoise import Model, fields


class Report(Model):
    floor = fields.ForeignKeyField('models.Floor', on_delete=fields.CASCADE)
    reason = fields.CharField(max_length=100)
    time_created = fields.DatetimeField(auto_now_add=True)
    time_updated = fields.DatetimeField(auto_now=True)
    dealed = fields.BooleanField(default=False, db_index=True)
    dealed_by = fields.ForeignKeyField('models.User', on_delete=fields.CASCADE, null=True)

    def __str__(self):
        return f"树洞#{self.floor.hole_id}, 帖子{self.floor}\n理由: {self.reason}"
