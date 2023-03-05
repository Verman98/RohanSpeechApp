using Microsoft.AspNetCore.Components;
using Microsoft.AspNetCore.Components.Web;
using Microsoft.AspNetCore.HttpOverrides;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.FileProviders;
using MudBlazor.Services;
using RohanSpeechApp.Interfaces;
using RohanSpeechApp.Services;

string currentDate = "28.02.2023 19:28";
Console.WriteLine(currentDate);

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.
builder.Services.AddRazorPages();
builder.Services.AddServerSideBlazor();
builder.Services.AddMvc(options => options.EnableEndpointRouting = false);

var currentDirectory = Environment.CurrentDirectory;
Console.WriteLine($"Current Directory: {currentDirectory}");
IFileProvider physicalFileProvider = new PhysicalFileProvider(currentDirectory);

builder.Services.AddSingleton<IFileProvider>(physicalFileProvider);
builder.Services.AddTransient<IVolumesRepository, VolumesRepository>();
builder.Services.AddSingleton<ISpeechSamplesProvider, SpeechSamplesProvider>(); 
builder.Services.AddSingleton<IGameService, GameService>();
builder.Services.AddScoped<IAuthenticationService, AuthentificationService>();


builder.Services.AddMudServices();

var app = builder.Build();


app.UseForwardedHeaders(new ForwardedHeadersOptions
{
    ForwardedHeaders = ForwardedHeaders.XForwardedFor | ForwardedHeaders.XForwardedProto
});

// Configure the HTTP request pipeline.
if (!app.Environment.IsDevelopment())
{
    app.UseExceptionHandler("/Error");
    // The default HSTS value is 30 days. You may want to change this for production scenarios, see https://aka.ms/aspnetcore-hsts.
    app.UseHsts();
}

//app.UseHttpsRedirection();

app.UseStaticFiles();

app.UseRouting();

app.UseMvcWithDefaultRoute();


app.MapBlazorHub();


app.UseEndpoints(endpoints =>
{
    endpoints.MapControllers();
});
app.MapFallbackToPage("/_Host");

app.Run();
