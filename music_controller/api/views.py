from django.shortcuts import render
from rest_framework import generics,status
from .serializers import RoomSerializer,CreateRoomSerializer,UpdateRoomSerializer
from .models import Room
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import JsonResponse

# Create your views here.
class RoomView(generics.ListAPIView):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer



class CreateRoomView(APIView):
    serializer_class=CreateRoomSerializer
    def post(self,request,format=None):
        #create a session if it does not exist already
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        
        serializer= self.serializer_class(data=request.data)
        if serializer.is_valid():
            guest_can_pause=serializer.data.get('guest_can_pause')
            votes_to_skip=serializer.data.get('votes_to_skip')
            host=self.request.session.session_key
            queryset=Room.objects.filter(host=host)
            #If host has already created a room
            if queryset.exists():
                room=queryset[0]
                room.guest_can_pause=guest_can_pause
                self.request.session['room_code']=room.code
                room.votes_to_skip=votes_to_skip
                room.save(update_fields=['guest_can_pause','votes_to_skip'])
                return Response(RoomSerializer(room).data, status=status.HTTP_200_OK)
            else:
                #create a new room
                room =Room(host=host,guest_can_pause=guest_can_pause,votes_to_skip=votes_to_skip)
                self.request.session['room_code']=room.code
                
                room.save()
                return Response(RoomSerializer(room).data, status=status.HTTP_201_CREATED)
        return Response({'Bad Request': 'Invalid data...'}, status=status.HTTP_400_BAD_REQUEST)


class RoomJoin(APIView):
    lookup_data_kwarg='code'
    serializer_class=RoomSerializer
    def post(self,request,format=None):
        #create a session if it does not exist already
        if not self.request.session.exists(self.request.session.session_key):
            self.request.session.create()
        code=request.data.get(self.lookup_data_kwarg)

        if code!=None:
            #find the room 
            room=Room.objects.filter(code=code)
            if len(room)>0:
                self.request.session['room_code']=code
                return Response({'message':'Room Joined'}, status=status.HTTP_200_OK)
        return Response({'Bad request':'Room Not Found'}, status=status.HTTP_404_NOT_FOUND)
        
        return Response({'Bad Request': 'Invalid,did not find the code key'}, status=status.HTTP_400_BAD_REQUEST)

        



class getCodeData(APIView):
    serializer_class=RoomSerializer
    lookup_url_kwarg='code'
    
    
    def get(self,request,format=None):
        code=request.GET.get(self.lookup_url_kwarg)
        if code!=None:
            room=Room.objects.filter(code=code)
            if len(room)>0:
                data=RoomSerializer(room[0]).data
                data['is_host']=self.request.session.session_key==room[0].host
                return Response(data,status=status.HTTP_200_OK)
            return Response({'Room Not Found':'INVALID ROOM CODE'},status=status.HTTP_404_NOT_FOUND)
        return Response({'Bad Request':'Code paramenter not found in request'},status=status.HTTP_)


class UserInRoom(APIView):
    
    def get(self,request,format=None):
        if not self.request.session.exists(self.request.session.session_key):
                self.request.session.create()
        data=self.request.session.get('room_code')
        return JsonResponse({
                'code':data
            },status=status.HTTP_200_OK)
        
        
class LeaveRoom(APIView):
    def post(self,request,format=None):
        if 'room_code' in self.request.session:
            self.request.session.pop('room_code')
            host_id =self.request.session.session_key
            room_results= Room.objects.filter(host=host_id)
            if len(room_results)>=0:
                room=room_results[0]
                room.delete()
        return Response({'Message':'Success'},status=status.HTTP_200_OK)   


class UpdateSettings(APIView):
    serializer_class=UpdateRoomSerializer
    def patch(self,request,format=None):
        if not self.request.session.exists(self.request.session.session_key):
                self.request.session.create()
        serializer=self.serializer_class(data=request.data)
        if serializer.is_valid():
                
                code=serializer.data.get('code')
                
                guest_can_pause=serializer.data.get('guest_can_pause')
                votes_to_skip=serializer.data.get('votes_to_skip')
                queryset=Room.objects.filter(code=code)
                if not queryset.exists():
                    return Response({"Msg":"Room Not Found"},status=status.HTTP_404_NOT_FOUND)
                
                room=queryset[0]
                user_id=self.request.session.session_key
                
                if room.host!=user_id:
                    return Response({"msg":'You are not the Host'},status=status.HTTP_403_FORBIDDEN)
                
                room.guest_can_pause=guest_can_pause
                room.votes_to_skip=votes_to_skip
                room.save(update_fields=['guest_can_pause','votes_to_skip'])
                return Response(RoomSerializer(room).data,status=status.HTTP_200_OK)
                
        return Response({"Bad Request":"Invalid Data..."},status=status.HTTP_400_BAD_REQUEST)
        