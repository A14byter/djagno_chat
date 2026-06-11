from channels.generic.websocket import AsyncWebsocketConsumer
import json

from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from .models import Chat, Message


class ChatConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f'chat_{self.room_name}'

        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):   # ✅ close_code اضافه شد
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name                # ✅ اصلاح: به جای channel_layer
        )

    async def receive(self, text_data):
        data = json.loads(text_data)

        event_type=data.get('type')
        if event_type == "chat_message":
            message = data['message']
            
            
            username = data['username']
            room = data['room']

            message_id = await self.save_message(
                username=username,
                room_slug=room,
                text=message,
                )


            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': message,
                    'message_id':message_id,
                    
                
                    'username': username,
                    'room': room,
                }
                    )




        elif event_type == 'read_message':
            await self.mark_message_as_read(
                room_slug=data['room'],
                message_id=data['message_id'],
                username=self.scope['user'].username
                
            )

            await self.channel_layer.group_send(
                self.room_group_name,{
                    'type':'read_message',
                    'message_id' : data['message_id'],
                    'reader': self.scope['user'].username,
                }
            )




        elif event_type == 'delete_message':
            room=data['room']
            message_id=data['message_id']

            deleted=await self.delete_a_message(room_slug=room,message_id=message_id,username=self.scope['user'].username)
            if deleted:

                await self.channel_layer.group_send(
                    self.room_group_name,{
                        'type':'delete_message',
                        'message_id':data['message_id'],
                        'user':self.scope['user'].username
                    }
                )




        elif event_type == 'edit_message':
            room=data['room']
            edited_text=data['edited_text']
            message_id=data['message_id']
            edited=await self.edit_a_message(username=self.scope['user'].username,edited_text=edited_text,room_slug=room,message_id=message_id)

            if edited:
                await self.channel_layer.group_send(
                    self.room_group_name,{
                        'type':'edit_message',
                        'room':room,
                        'message_id' : message_id,
                        'edited_text':edited_text,
                        'user':self.scope['user'].username

                        
                    }
                )

        elif event_type == 'reply':
            room=data['room']
            username=self.scope['user'].username
            target_message_id=data['target_message_id']
            the_message=data['the_message']

            reply_result=await self.reply_to_message(
                username=username,
                room_slug=room,
                target_message_id=target_message_id,
                the_message=the_message
            )
            if reply_result:
                await self.channel_layer.group_send(
                    self.room_group_name,{
                        'type':'reply',
                        'room':room,
                        'user':username,
                        'target_message_id':target_message_id,
                        'the_message':the_message,
                        'message_id':reply_result['message_id'],
                        'reply_to_user': reply_result['reply_to_user'],
                        'reply_to_text': reply_result['reply_to_text']

                    }
                )







    async def chat_message(self, event):
        message = event['message']
        username = event['username']
        
        
        
       
        
        await self.send(text_data=json.dumps({   
            'message': message,
            'message_id':event.get('message_id'),
            'photo' : event.get('photo'),
            'file' : event.get('file'),
            'username': username,
            'room':event.get('room'),
        }))

    async def read_message(self,event):
        await self.send(text_data=json.dumps({
            'type':'read_message',
            'message_id' :event['message_id'],
            'reader': event['reader'],
        }))


    async def delete_message(self,event):
        await self.send(text_data=json.dumps({
            'type':'delete_message',
            'message_id':event['message_id'],
            'user':event['user'],
        }))        
    

    async def edit_message(self,event):
        await self.send(text_data=json.dumps({
            'type':'edit_message',
            'message_id':event['message_id'],
            'user':event['user'],
            'edited_text':event['edited_text']

        }))

    async def reply(self,event):
        await self.send(text_data=json.dumps({
        'type':'reply',
        'user':event['user'],
        'target_message_id':event['target_message_id'],
        'the_message':event['the_message'],
        'reply_to_user':event['reply_to_user'],
        'reply_to_text':event['reply_to_text'],
        'message_id':event['message_id']

        }))
        


        
    @database_sync_to_async
    def save_message(self, username, room_slug, text):

        user = User.objects.get(username=username)

        chat = Chat.objects.get(slug=room_slug)

        msg= Message.objects.create(
            user=user,
            chat=chat,
            text=text,
           
        )
        return msg.id


    @database_sync_to_async
    def mark_message_as_read(self,room_slug,message_id,username):
        chat=Chat.objects.get(slug=room_slug)

        Message.objects.filter(
            chat=chat,read=False,id=message_id
        ).exclude(user__username=username).update(read=True)


    @database_sync_to_async
    def delete_a_message(self,room_slug,message_id,username):
        
        chat=Chat.objects.get(slug=room_slug)

        message=Message.objects.filter(
            id=message_id,
            chat=chat,
            user__username=username).first()
       
        if not message:
            return False

        if message.photo:
            message.photo.delete(save=False)
        
        if message.file:
            message.file.delete(save=False)

        message.delete()
        return True


    
    @database_sync_to_async
    def edit_a_message(self,room_slug,message_id,username,edited_text):
        chat=Chat.objects.get(slug=room_slug,users__username=username)

        message=Message.objects.filter(user__username=username,chat=chat,id=message_id).first()
        if not message:
            return False
           
        else:
            message.text=edited_text
            message.save()
            return True


    @database_sync_to_async
    def reply_to_message(self,room_slug,username,target_message_id,the_message):
        user=User.objects.filter(username=username).first()
        
        chat=Chat.objects.get(slug=room_slug,users__username=username)

        target_message=Message.objects.filter(chat=chat,id=target_message_id).first()
        if not target_message:
            return False

        else:
            new_message=Message.objects.create(
                user=user,
                chat=chat,
                text=the_message,
                reply_to=target_message
            )
            return {
                'message_id':new_message.id,
                'reply_to_user':target_message.user.username,
                'reply_to_text':target_message.text[:30] if target_message.text else 'file'
            }
