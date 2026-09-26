from rest_framework import status, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.http import JsonResponse
from .models import Drop
from .serializers import DropSerializer, ReservationSerializer
from .services import (
    ActiveReservationExistsError,
    DropNotStartedError,
    ReservationError,
    SoldOutError,
    create_drop,
    create_reservation,
    delete_drop,
    restore_drop,
    update_drop,
)


class DropViewSet(viewsets.ModelViewSet):

    queryset = Drop.objects.filter(
        is_deleted=False
    )

    serializer_class = DropSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):

        serializer = self.get_serializer(
            data=request.data
        )

        serializer.is_valid(
            raise_exception=True
        )

        drop = create_drop(
            validated_data=serializer.validated_data
        )

        return Response(
            self.get_serializer(drop).data,
            status=status.HTTP_201_CREATED,
        )

    def update(
        self,
        request,
        *args,
        **kwargs,
    ):

        drop = self.get_object()

        serializer = self.get_serializer(
            drop,
            data=request.data,
        )

        serializer.is_valid(
            raise_exception=True
        )

        drop = update_drop(
            drop=drop,
            validated_data=serializer.validated_data,
        )

        return Response(
            self.get_serializer(drop).data,
            status=status.HTTP_200_OK,
        )

    def partial_update(
        self,
        request,
        *args,
        **kwargs,
    ):

        drop = self.get_object()

        serializer = self.get_serializer(
            drop,
            data=request.data,
            partial=True,
        )

        serializer.is_valid(
            raise_exception=True
        )

        drop = update_drop(
            drop=drop,
            validated_data=serializer.validated_data,
        )

        return Response(
            self.get_serializer(drop).data,
            status=status.HTTP_200_OK,
        )

    def destroy(
        self,
        request,
        *args,
        **kwargs,
    ):

        drop = self.get_object()

        delete_drop(
            drop=drop
        )

        return Response(
            status=status.HTTP_204_NO_CONTENT
        )

    def restore(
        self,
        request,
        *args,
        **kwargs,
    ):

        drop = Drop.objects.filter(
            id=kwargs["pk"],
            is_deleted=True,
        ).first()

        if not drop:
            return Response(
                {
                    "error": "DROP_NOT_FOUND",
                    "message": (
                        "Deleted drop not found."
                    ),
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        drop = restore_drop(
            drop=drop
        )

        return Response(
            {
                "message": (
                    "Drop restored successfully."
                ),
                "drop": DropSerializer(
                    drop
                ).data,
            },
            status=status.HTTP_200_OK,
        )


class CreateReservationAPIView(APIView):

    permission_classes = [IsAuthenticated]

    def post(self, request, drop_id):

        try:
            reservation = create_reservation(
                drop_id=drop_id,
                user=request.user,
            )

        except Drop.DoesNotExist:
            return Response(
                {
                    "error": "DROP_NOT_FOUND",
                    "message": "Drop not found.",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        except DropNotStartedError as exc:
            return Response(
                {
                    "error": "DROP_NOT_STARTED",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        except ActiveReservationExistsError as exc:
            return Response(
                {
                    "error": "ACTIVE_RESERVATION_EXISTS",
                    "message": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )

        except SoldOutError as exc:
            return Response(
                {
                    "error": "SOLD_OUT",
                    "message": str(exc),
                },
                status=status.HTTP_409_CONFLICT,
            )

        except ReservationError as exc:
            return Response(
                {
                    "error": "RESERVATION_ERROR",
                    "message": str(exc),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            ReservationSerializer(
                reservation
            ).data,
            status=status.HTTP_201_CREATED,
        )
        
def health_check(request):
    return JsonResponse({
        "status": "ok",
        "service": "DropCart",
    })