using Microsoft.Extensions.FileProviders;

namespace RohanSpeechApp.Interfaces
{
    public interface IVolumesRepository
    {
        PhysicalFileProvider FileProvider { get; }

        bool AudioSampleExists(string sample);

        string NextFileName(string sample);

        string GetGameConfigPath();

        IDirectoryContents GetSpeechSamplesDirectoryContents();

        string GetPasswordFilePath();
    }
}
