'use client'

import { useState } from "react"
import { Button } from "./ui/button"
import { InfoIcon, X } from "lucide-react"
import { ScrollArea } from "./ui/scroll-area"
import Image from "next/image"
import Link from "next/link"
import { Accordion } from "@radix-ui/react-accordion"
import { AccordionContent, AccordionItem, AccordionTrigger } from "./ui/accordion"

export default function Info() {
  const [isOpen, setIsOpen] = useState(false)

  const samples = [
    {
      id: 1,
      name: "Roubion",
      type: "Atmospheric",
      sol: 164,
      date: "Aug. 6, 2021",
      location: "Polygon Valley",
      rockType: "n/a",
      description: "The first atmospheric sample collected, capturing Martian gases for analysis of the planet's atmospheric composition.",
      currentLocation: "Sample Depot"
    },
    {
      id: 2,
      name: "Montdenier",
      type: "Rock Core",
      sol: 194,
      date: "Sept. 6, 2021",
      location: "Artuby Ridge (Rochette)",
      rockType: "Igneous",
      description: "Fine-grained igneous rock from the crater floor, representing ancient volcanic bedrock of Jezero Crater.",
      currentLocation: "Sample Depot"
    },
    {
      id: 3,
      name: "Montagnac",
      type: "Rock Core",
      sol: 196,
      date: "Sept. 8, 2021",
      location: "Artuby Ridge (Rochette)",
      rockType: "Igneous",
      description: "Second core from Rochette rock, providing additional material from the ancient igneous formation.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 4,
      name: "Salette",
      type: "Rock Core",
      sol: 262,
      date: "Nov. 15, 2021",
      location: "South Séítah (Brac)",
      rockType: "Igneous",
      description: "Sample from South Séítah, an area with some of the oldest rocks in Jezero Crater.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 5,
      name: "Coulettes",
      type: "Rock Core",
      sol: 271,
      date: "Nov. 24, 2021",
      location: "South Séítah (Brac)",
      rockType: "Igneous",
      description: "Second sample from Brac rock, showing evidence of water-rock interaction in the past.",
      currentLocation: "Sample Depot"
    },
    {
      id: 6,
      name: "Robine",
      type: "Rock Core",
      sol: 298,
      date: "Dec. 22, 2021",
      location: "South Séítah (Issole)",
      rockType: "Igneous",
      description: "Collected from Issole rock, containing olivine-rich minerals that formed in ancient magma.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 7,
      name: "Malay",
      type: "Rock Core",
      sol: 337,
      date: "Jan. 31, 2022",
      location: "South Séítah (Issole)",
      rockType: "Igneous",
      description: "Second core from Issole, providing additional material from this olivine-bearing formation.",
      currentLocation: "Sample Depot"
    },
    {
      id: 8,
      name: "Ha'ahóni",
      type: "Rock Core",
      sol: 371,
      date: "March 7, 2022",
      location: "Octavia E. Butler Landing / Ch'ał outcrop (Sid)",
      rockType: "Igneous",
      description: "Collected near the landing site from an outcrop showing evidence of ancient magmatic processes.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 9,
      name: "Atsá",
      type: "Rock Core",
      sol: 377,
      date: "March 13, 2022",
      location: "Octavia E. Butler Landing / Ch'ał outcrop (Sid)",
      rockType: "Igneous",
      description: "Second sample from the Sid feature, providing paired analysis potential with Ha'ahóni.",
      currentLocation: "Sample Depot"
    },
    {
      id: 10,
      name: "Swift Run",
      type: "Rock Core",
      sol: 490,
      date: "July 7, 2022",
      location: "Delta Front (Skinner Ridge)",
      rockType: "Sedimentary",
      description: "First sedimentary sample from the delta front, showing evidence of ancient water flow and sediment deposition.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 11,
      name: "Skyland",
      type: "Rock Core",
      sol: 495,
      date: "July 12, 2022",
      location: "Delta Front (Skinner Ridge)",
      rockType: "Sedimentary",
      description: "Second sample from Skinner Ridge, part of the ancient river delta system.",
      currentLocation: "Sample Depot"
    },
    {
      id: 12,
      name: "Hazeltop",
      type: "Rock Core",
      sol: 509,
      date: "July 27, 2022",
      location: "Delta Front (Wildcat Ridge)",
      rockType: "Sedimentary",
      description: "Fine-grained sedimentary rock from Wildcat Ridge, potentially preserving organic compounds.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 13,
      name: "Bearwallow",
      type: "Rock Core",
      sol: 516,
      date: "Aug. 3, 2022",
      location: "Delta Front (Wildcat Ridge)",
      rockType: "Sedimentary",
      description: "Second core from Wildcat Ridge, showing layered sediments deposited in ancient aqueous environments.",
      currentLocation: "Sample Depot"
    },
    {
      id: 14,
      name: "Shuyak",
      type: "Rock Core",
      sol: 575,
      date: "Oct. 2, 2022",
      location: "Delta Front (Amalik)",
      rockType: "Sedimentary",
      description: "Sedimentary sample from Amalik feature, showing evidence of past water activity.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 15,
      name: "Mageik",
      type: "Rock Core",
      sol: 619,
      date: "Nov. 16, 2022",
      location: "Delta Front (Amalik)",
      rockType: "Sedimentary",
      description: "Second sample from Amalik, providing paired analysis with Shuyak.",
      currentLocation: "Sample Depot"
    },
    {
      id: 16,
      name: "Kukaklek",
      type: "Rock Core",
      sol: 631,
      date: "Nov. 29, 2022",
      location: "Delta Front (Hidden Harbor)",
      rockType: "Sedimentary",
      description: "Sample from Hidden Harbor feature within the delta formation.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 17,
      name: "Atmo Mountain",
      type: "Regolith",
      sol: 634,
      date: "Dec. 2, 2022",
      location: "Delta Front (Observation Mountain)",
      rockType: "Mixed sedimentary and igneous grains",
      description: "Regolith sample containing loose surface material with mixed rock fragments.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 18,
      name: "Crosswind Lake",
      type: "Regolith",
      sol: 639,
      date: "Dec. 7, 2022",
      location: "Delta Front (Observation Mountain)",
      rockType: "Mixed sedimentary and igneous grains",
      description: "Second regolith sample from Observation Mountain area.",
      currentLocation: "Sample Depot"
    },
    {
      id: 19,
      name: "Melyn",
      type: "Rock Core",
      sol: 749,
      date: "March 30, 2023",
      location: "Upper Fan (Berea)",
      rockType: "Sedimentary",
      description: "Sample from the upper fan region, representing later depositional periods in the delta.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 20,
      name: "Otis Peak",
      type: "Rock Core",
      sol: 832,
      date: "June 23, 2023",
      location: "Upper Fan (Emerald Lake)",
      rockType: "Sedimentary",
      description: "Upper fan sample showing continued sedimentary deposition in the ancient lake environment.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 21,
      name: "Pilot Mountain",
      type: "Rock Core",
      sol: 913,
      date: "Sept. 15, 2023",
      location: "Upper Fan (Dream Lake)",
      rockType: "Sedimentary",
      description: "Sample from Dream Lake feature in the upper delta fan.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 22,
      name: "Pelican Point",
      type: "Rock Core",
      sol: 923,
      date: "Sept. 25, 2023",
      location: "Margin Unit (Hans Amundsen Memorial Workspace)",
      rockType: "Sedimentary",
      description: "Sample from the margin unit, showing transition between different geological formations.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 23,
      name: "Lefroy Bay",
      type: "Rock Core",
      sol: 949,
      date: "Oct. 21, 2023",
      location: "Margin Unit (Turquoise Bay)",
      rockType: "Sedimentary",
      description: "Margin unit sample providing insights into the edges of the delta system.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 24,
      name: "Comet Geyser",
      type: "Rock Core",
      sol: 1088,
      date: "March 12, 2024",
      location: "Margin Unit (Bunsen Peak)",
      rockType: "Silica-cemented Carbonate",
      description: "Unique carbonate sample with silica cement, indicating specific water chemistry conditions.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 25,
      name: "Sapphire Canyon",
      type: "Rock Core",
      sol: 1215,
      date: "July 21, 2024",
      location: "Neretva Vallis (Cheyava Falls)",
      rockType: "Sedimentary",
      description: "Highly significant sample with potential biosignatures, containing features that may indicate ancient microbial life.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 26,
      name: "Silver Mountain",
      type: "Rock Core",
      sol: 1401,
      date: "Jan. 28, 2025",
      location: "Crater Rim - Witch Hazel Hill (Shallow Bay)",
      rockType: "Igneous/impactite",
      description: "Sample from the crater rim showing impact-related or igneous processes.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 27,
      name: "Green Gardens",
      type: "Rock Core",
      sol: 1433,
      date: "March 2, 2025",
      location: "Crater Rim - Witch Hazel Hill (Tablelands)",
      rockType: "Serpentinite",
      description: "Rare serpentinite sample formed by water-rock alteration, potentially important for understanding habitability.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 28,
      name: "Main River",
      type: "Rock Core",
      sol: 1441,
      date: "March 10, 2025",
      location: "Crater Rim - Witch Hazel Hill (Broom Point)",
      rockType: "Igneous/impactite",
      description: "Crater rim sample showing evidence of impact or igneous origin.",
      currentLocation: "Perseverance Rover"
    },
    {
      id: 29,
      name: "Bell Island",
      type: "Rock Core",
      sol: "TBD",
      date: "Not yet sealed",
      location: "Crater Rim - Witch Hazel Hill (Pine Pond)",
      rockType: "Igneous/impactite",
      description: "Recently collected sample awaiting sealing, from the crater rim region.",
      currentLocation: "Perseverance Rover"
    },
    // {
    //   id: 30,
    //   name: "Gallants",
    //   type: "Rock Core",
    //   sol: "TBD",
    //   date: "Not yet sealed",
    //   location: "Crater Rim - Krokodillen (Salmon Point)",
    //   rockType: "Igneous or sedimentary",
    //   description: "Most recent collection from the Krokodillen area of the crater rim.",
    //   currentLocation: "Perseverance Rover"
    // }
  ];

  return (
    <div className="relative">
      {/* Toggle Button */}
      <Button
        hidden={isOpen}
        onClick={() => setIsOpen(!isOpen)}
        className="m-2 relative overflow-hidden bg-black/20 backdrop-blur-xl border border-white/20 text-white hover:bg-black/30 transition-all duration-500 shadow-xl hover:shadow-2xl hover:scale-105 rounded-2xl px-6 py-3 group"
      >
        <div className="absolute inset-0 bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500"></div>
        <div className="relative flex items-center gap-2">
          <InfoIcon className="w-4 h-4 transition-transform duration-300 group-hover:rotate-12" />
          <span className="font-medium">Show Insights</span>
        </div>
      </Button>

      {/* Black & White Glass Info Card */}
      {isOpen && (
        <div className="left-0 h-screen over w-96 z-50 animate-in slide-in-from-top-5 duration-500">
          <div className="h-screen">
            {/* Glass morphism layer */}
            <div className="absolute inset-0 backdrop-blur-2xl bg-black/40 border border-white/20"></div>

            {/* Content container */}
            <div className="relative h-full flex flex-col">
              {/* Header */}
              <div className="flex items-center justify-between p-6 border-b border-white/10">
                <h2 className="text-xl font-bold text-white">
                  Mars 2020: Perseverance Mission
                </h2>
                <Button
                  onClick={() => setIsOpen(false)}
                  variant="ghost"
                  size="sm"
                  className="text-white/70 hover:text-white hover:bg-white/10 rounded-full p-2 transition-all duration-300"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
              <ScrollArea className="h-full overflow-hidden">
                <Accordion type="single" collapsible defaultValue="item-0" className="h-full flex flex-col">

                  {/* Mission Overview */}
                  <AccordionItem value="item-0" >
                    <AccordionTrigger className="p-6 border-b border-white/10">
                      <p className="text-lg font-semibold text-white/90">
                        Mission Overview
                      </p>
                    </AccordionTrigger>
                    <AccordionContent className="p-0 border-b border-white/10">

                      {/* Content */}
                      <div className="flex-1 p-6 space-y-6 overflow-y-auto min-h-0">

                        {/* Perseverance Rover Info */}
                        <div className="space-y-3">
                          <h3 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                            <div className="w-2 h-2 bg-white/60 rounded-full"></div>
                            Perseverance Rover
                          </h3>
                          <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                            <p className="text-white/80 text-sm leading-relaxed">
                              The rover's primary goal is to <span className="font-bold">seek signs of ancient microbial life</span> (biosignatures) and collect core samples of Martian rock and regolith for potential pickup by a future <span className="font-bold">Mars Sample Return</span> mission.
                              <br /><br />
                              <span className="font-bold">Launch:</span> July 30, 2020 • <span className="font-bold">Landing:</span> Feb. 18, 2021
                            </p>
                            <Image src={'/rover-1.webp'} height={200} width={500} alt="rover" />
                          </div>
                        </div>

                        {/* Jezero Crater Landing Site */}
                        <div className="space-y-3">
                          <h3 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                            <div className="w-2 h-2 bg-200/60 rounded-full"></div>
                            Jezero Crater Landing Site
                          </h3>
                          <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                            <p className="text-white/80 text-sm leading-relaxed">
                              Jezero Crater was chosen because scientists believe it was once flooded with water, containing an <span className="font-bold">ancient river delta</span>. It holds <span className="font-bold">carbonate minerals</span> and <span className="font-bold">clay deposits</span> that are ideal for preserving evidence of past microbial life.
                            </p>
                            <Image src={'/crater.webp'} height={400} width={400} alt="jazero crater" />
                          </div>
                        </div>

                        {/* Key Science Objectives */}
                        <div className="space-y-3">
                          <h3 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                            <div className="w-2 h-2 bg-white/60 rounded-full"></div>
                            Four Science Objectives
                          </h3>
                          <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                            <ul className="list-disc list-inside text-white/80 text-sm leading-relaxed space-y-1 ml-4">
                              <li>Study Mars' Past Habitability.</li>
                              <li>Seek Signs of Past Microbial Life.</li>
                              <li>Collect and Cache Martian Samples.</li>
                              <li>Prepare for Future Human Missions (testing MOXIE).</li>
                            </ul>
                          </div>
                        </div>

                        {/* Ingenuity Mars Helicopter */}
                        <div className="space-y-3">
                          <h3 className="text-lg font-semibold text-white/90 flex items-center gap-2">
                            <div className="w-2 h-2 bg-white/60 rounded-full"></div>
                            Ingenuity Mars Helicopter
                          </h3>
                          <div className="bg-white/5 rounded-xl p-4 border border-white/10">
                            <p className="text-white/80 text-sm leading-relaxed">
                              Strapped to Perseverance's belly, Ingenuity was a technology demonstration that successfully achieved the <span className="font-bold">first powered, controlled flight on another planet</span>, completing 72 historic flights.
                            </p>
                          </div>
                        </div>
                        <Link className="text-blue-400 underline text-sm" href="https://science.nasa.gov/mission/mars-2020-perseverance/" target="_blank">Learn more about the mission</Link>
                        <br />
                        <Link className="text-blue-400 underline text-sm" href="https://science.nasa.gov/mission/mars-2020-perseverance/mars-rock-samples/" target="_blank">Learn more about all rock samples</Link>

                      </div>
                    </AccordionContent>
                  </AccordionItem>


                  {samples.map((sample) => (
                    <AccordionItem
                      key={sample.id}
                      value={`item-${sample.id}`}
                      className="bg-white/5 backdrop-blur-sm rounded-lg border border-white/10"
                    >
                      <AccordionTrigger className="px-6 py-4 hover:bg-white/5">
                        <div className="flex items-center gap-4 text-left">
                          <div className="bg-blue-500/20 rounded-full w-10 h-10 flex items-center justify-center flex-shrink-0">
                            <span className="text-blue-300 font-bold">{sample.id}</span>
                          </div>
                          <div>
                            <div className="font-semibold text-lg">{sample.name}</div>
                            <div className="text-sm text-white/60">{sample.date}</div>
                          </div>
                        </div>
                      </AccordionTrigger>
                      <AccordionContent className="px-6 pb-6">
                        <div className="space-y-4 pt-4">
                          <div className="grid md:grid-cols-2 gap-4">
                            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                              <div className="text-sm text-white/60 mb-1">Sample Type</div>
                              <div className="font-semibold">{sample.type}</div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                              <div className="text-sm text-white/60 mb-1">Rock Type</div>
                              <div className="font-semibold">{sample.rockType}</div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                              <div className="text-sm text-white/60 mb-1">Sol</div>
                              <div className="font-semibold">{sample.sol}</div>
                            </div>
                            <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                              <div className="text-sm text-white/60 mb-1">Current Location</div>
                              <div className="font-semibold">{sample.currentLocation}</div>
                            </div>
                          </div>

                          <div className="bg-white/5 rounded-lg p-4 border border-white/10">
                            <div className="text-sm text-white/60 mb-2">Location</div>
                            <div className="font-semibold mb-3">{sample.location}</div>
                            <div className="text-sm text-white/80 leading-relaxed">
                              {sample.description}
                            </div>
                          </div>
                        </div>
                      </AccordionContent>
                    </AccordionItem>
                  ))}
                </Accordion>

              </ScrollArea>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}