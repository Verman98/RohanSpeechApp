using Microsoft.Extensions.FileProviders;
using RohanSpeechApp.Interfaces;

namespace RohanSpeechApp.Services
{
    public class VolumesRepository : IVolumesRepository
    {
        /// <summary>
        /// Uploads will be saved as "sample name"+"-$index"+".wav"
        /// </summary>
        /// 
        private readonly PhysicalFileProvider fileProvider;
        public PhysicalFileProvider FileProvider => fileProvider;

        private const string BASEWEBPATH = "wwwroot";
        private const string UPLOADSNAME = "uploads";
        private const string DATANAME = "cfg-data";
        private const string SPEECHSAMPLESFOLDER = "samples";


        public VolumesRepository(IFileProvider fileProvider)
        {
            this.fileProvider = (PhysicalFileProvider)fileProvider;
        }


        #region Audio files
        public bool AudioSampleExists(string sample)
        {
            string folderPath = Path.Combine(BASEWEBPATH, UPLOADSNAME);

            IDirectoryContents directoryContents = FileProvider.GetDirectoryContents(folderPath);

            foreach(var directoryContent in directoryContents)
            {
                if(directoryContent.Name.Split("-")[0] == sample) return true;
            }

            return false;
        }

        public string NextFileName(string sample)
        {
            int lastIndex = 0;

            if (AudioSampleExists(sample))
            {
                string folderPath = Path.Combine(BASEWEBPATH, UPLOADSNAME);

                IDirectoryContents directoryContents = FileProvider.GetDirectoryContents(folderPath);

                foreach (var directoryContent in directoryContents)
                {
                    string[] splittedName = directoryContent.Name.Split("-");
                
                    if (splittedName[0] == sample && int.Parse(splittedName[1].Split(".")[0]) > lastIndex)
                    {
                        lastIndex = int.Parse(splittedName[1].Split(".")[0]);
                    }
                }

                lastIndex++;
            }

            return sample + "-" + lastIndex + ".wav";
        }
        #endregion

        public string GetPasswordFilePath() => Path.Combine(FileProvider.Root, DATANAME, "password.json");
        public string GetGameConfigPath() => Path.Combine(FileProvider.Root, DATANAME, "gameconfig.json");

        public IDirectoryContents GetSpeechSamplesDirectoryContents() => FileProvider.GetDirectoryContents(Path.Combine(DATANAME, SPEECHSAMPLESFOLDER));
    }
}
