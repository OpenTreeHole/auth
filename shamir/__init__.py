from tortoise import Model, fields

import models


class ShamirEmail(Model):
    """
    shamir secret sharing(SSS) shares of user email
    """
    id = fields.IntField(pk=True)
    key = fields.TextField()
    user: fields.ForeignKeyRelation['models.User'] = fields.ForeignKeyField('models.User', related_name='shamir_emails')
    encrypted_by = fields.CharField(max_length=128)

    class Meta:
        table = "shamir_email"
