using RohanSpeechApp.Interfaces;
using System.Diagnostics.Metrics;

namespace RohanSpeechApp.Services
{
    public class SpeechSamplesProvider : ISpeechSamplesProvider
    {
        private readonly IVolumesRepository _volumesRepository;

        private List<string> samples = new List<string>();  
        
        public SpeechSamplesProvider(IVolumesRepository volumesRepository)
        {
            _volumesRepository = volumesRepository;

            samples = GetAllSamples();
        }


        public List<string> GetAllSamples()
        {
            List<string> samples = new List<string>();

            foreach(var directoryContent in _volumesRepository.GetSpeechSamplesDirectoryContents())
            {
                var sampleFromFile = GetAllSamplesFromFile(directoryContent.PhysicalPath);

                samples.AddRange(sampleFromFile);
            }

            return samples;
        }

        public List<string> GetAllSamplesFromFile(string filePath)
        {
            List<string> samples = new List<string>();

            // Read the file and display it line by line.  
            foreach (string line in File.ReadLines(filePath))
            {
                if (string.IsNullOrWhiteSpace(line))
                {
                    continue;

                }

                samples.Add(line);
                Console.WriteLine(line);
            }

            return samples;
        }

        public string GetRandomSample()
        {
            Random rnd = new Random();
            int num = rnd.Next(samples.Count);

            return samples[num];
        }

        public string GetSpecificSample(int index)
        {
            return samples[index];
        }
    }
}
