import json
import re

from django.shortcuts import render
from django.db.models import Q
from rest_framework import viewsets
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response

from . import utils
from .models import MovieInfo, OneLineCritic
from .serializers import (
    MovieInfoSerializers,
    OneLineCriticSerializers,
    OneLineCriticCreateUpdateSerializers,
)


class SerachMovieAPIView(APIView):
    def post(self, request):
        query = json.loads(request.body)["query"]
        query = re.sub(" ", "", query)
        res = utils.getMovieInfo(query)

        if res.status_code == 200:
            data = res.data
            if data["Data"][0]["Count"] == 0:
                return Response({"message": "검색 결과가 없습니다."})
            utils.saveMovieInfo(data)

        queryset = MovieInfo.objects.filter(Q(searchTitle__icontains=query))
        serializer = MovieInfoSerializers(queryset, many=True)
        return Response(serializer.data)


class OneLineCriticViewSet(viewsets.ModelViewSet):
    queryset = OneLineCritic.objects.all()
    serializer_class = OneLineCriticSerializers

    def list(self, request, *args, **kwargs):
        pk = self.kwargs["movie_id"]
        queryset = OneLineCritic.objects.filter(movie__id=pk)
        serializer = OneLineCriticSerializers(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = OneLineCriticCreateUpdateSerializers(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=201)

    def perform_create(self, serializer):
        """
        create method에서 실제로 데이터베이스에 값을 저장하는 method.
        "url: /movieinfo/detail/<int:movie_id>/onelinecritic/"에서 'movie_id'를 통해,
        MovieInfo의 id == movie_id인 레코드를 OneLineCritic의 movie의 외래키로 연결시키도록 한다.
        이때 사용자로부터 movie에 대한 값은 받지 않으며, url을 통해서만 받는다.

        나머지 content와 startpoin의 값은 사용자가 입력한 값을 받는다.
        """
        req = self.request.data
        content = req["content"]
        starpoint = req["starpoint"]
        serializer.save(
            content=content,
            starpoint=starpoint,
            movie=MovieInfo.objects.get(id=self.kwargs["movie_id"]),
        )

    def retrieve(self, request, *args, **kwargs):
        """
        url예시: /movieinfo/detail/<int:movie_id>/onelinecritic/<int:pk>/
        model: OneLineCritic
        serializer: OneLineCriticSerializers

        현재 주소의 movie_id 값과 pk 값을 통해 OneLineCritic 모델의 movie==movie_id 이고,
        모델의 id==pk 인 항목을 objects.get을 통해 찾는다.
        해당 항목이 있다면 serializer를 통해 직렬화된 값을 응답,
        그렇지 않으면 400에러를 보낸다.
        """
        pk = self.kwargs["pk"]
        movie_id = self.kwargs["movie_id"]
        try:
            instance = OneLineCritic.objects.get(Q(id=pk) & Q(movie__id=movie_id))
            serializer = OneLineCriticSerializers(instance)
            return Response(serializer.data)
        except:
            errorMessage = {"message": "잘못된 응답입니다."}
            return Response(errorMessage, status=status.HTTP_400_BAD_REQUEST)

    def partial_update(self, request, *args, **kwargs):
        pk = self.kwargs["pk"]
        movie_id = self.kwargs["movie_id"]
        try:
            instance = OneLineCritic.objects.get(Q(id=pk) & Q(movie__id=movie_id))
            data = request.data
            serializer = OneLineCriticCreateUpdateSerializers(
                instance=instance, data=data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_202_ACCEPTED)
        except:
            errorMessage = {"message": "잘못된 응답입니다."}
            return Response(errorMessage, status=status.HTTP_400_BAD_REQUEST)

    def perform_update(self, serializer):
        req = self.request.data
        content = req["content"]
        starpoint = req["starpoint"]
        print(self.kwargs["movie_id"])
        serializer.save(
            content=content,
            starpoint=starpoint,
            movie=MovieInfo.objects.get(id=self.kwargs["movie_id"]),
        )

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)


class MovieInfoViewSet(viewsets.ModelViewSet):
    queryset = MovieInfo.objects.all()
    serializer_class = MovieInfoSerializers
