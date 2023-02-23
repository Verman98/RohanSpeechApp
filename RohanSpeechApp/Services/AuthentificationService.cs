using Microsoft.JSInterop;
using RohanSpeechApp.Interfaces;

namespace RohanSpeechApp.Services
{
    public class AuthentificationService : IAuthenticationService
    {
        private readonly string PINCOOKIEKEY = "PinCookie";
        private readonly IJSRuntime _jsRuntime;

        public AuthentificationService(IJSRuntime jsRuntime)
        {
            this._jsRuntime = jsRuntime; 
        }

        public string AuthPIN { get; set; } = "12051998";

        public async Task<string> GetSavedAuthAsync()
        {
            string savedPin = await _jsRuntime.InvokeAsync<string>("getCookie", PINCOOKIEKEY);

            return savedPin;
        }

        public async Task SaveAuthAsync(string pin)
        {
            await _jsRuntime.InvokeVoidAsync("addCookie", PINCOOKIEKEY, pin);
        }
    }
}
