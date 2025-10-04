# syntax=docker/dockerfile:1.5

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS restore
WORKDIR /src
COPY UKNF.Backend.csproj ./
RUN dotnet restore

FROM restore AS build
COPY . .
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
ENV ASPNETCORE_URLS=http://0.0.0.0:4000
ENV ASPNETCORE_ENVIRONMENT=Production
COPY --from=build /app/publish ./
EXPOSE 4000
ENTRYPOINT ["dotnet", "UKNF.Backend.dll"]

FROM mcr.microsoft.com/dotnet/sdk:8.0 AS dev
WORKDIR /app
ENV ASPNETCORE_URLS=http://0.0.0.0:4000
ENV ASPNETCORE_ENVIRONMENT=Development
COPY . .
EXPOSE 4000
CMD ["dotnet", "watch", "run", "--urls", "http://0.0.0.0:4000"]
