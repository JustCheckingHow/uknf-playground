using System.Text.Json;
using System.Text.Json.Serialization;
using UKNF.Backend.Services.Admin;
using UKNF.Backend.Services.Auth;
using UKNF.Backend.Services.Communication;

var builder = WebApplication.CreateBuilder(args);

builder.Services
    .AddControllers()
    .AddJsonOptions(options =>
    {
        options.JsonSerializerOptions.PropertyNamingPolicy = JsonNamingPolicy.CamelCase;
        options.JsonSerializerOptions.DictionaryKeyPolicy = JsonNamingPolicy.CamelCase;
        options.JsonSerializerOptions.DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull;
        options.JsonSerializerOptions.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.CamelCase));
    });

builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy
            .AllowAnyOrigin()
            .AllowAnyMethod()
            .AllowAnyHeader();
    });
});

// Communication module services
builder.Services.AddSingleton<ReportsService>();
builder.Services.AddSingleton<MessagesService>();
builder.Services.AddSingleton<CasesService>();
builder.Services.AddSingleton<AnnouncementsService>();
builder.Services.AddSingleton<LibraryService>();
builder.Services.AddSingleton<FaqService>();
builder.Services.AddSingleton<EntitiesService>();

// Auth module services
builder.Services.AddSingleton<AuthService>();
builder.Services.AddSingleton<AccessRequestsService>();
builder.Services.AddSingleton<SessionService>();

// Admin module services
builder.Services.AddSingleton<UsersService>();
builder.Services.AddSingleton<RolesService>();
builder.Services.AddSingleton<PasswordPolicyService>();

var app = builder.Build();

app.UseCors();
app.MapControllers();

var port = Environment.GetEnvironmentVariable("PORT");
if (int.TryParse(port, out var parsedPort) && parsedPort > 0)
{
    app.Urls.Add($"http://0.0.0.0:{parsedPort}");
}
else
{
    app.Urls.Add("http://0.0.0.0:4000");
}

app.Run();
