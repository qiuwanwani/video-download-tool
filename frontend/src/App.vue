<template>
  <div class="min-h-screen font-['Open_Sans']">
    <!-- 导航栏 -->
    <nav class="bg-[#0F0F23] bg-opacity-95 backdrop-blur-sm fixed top-4 left-4 right-4 z-50 rounded-xl transition-all duration-300" style="box-shadow: var(--shadow-lg);">
      <div class="max-w-7xl mx-auto px-6 py-4">
        <div class="flex justify-between items-center">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-lg flex items-center justify-center shadow-lg" :class="isDarkMode ? 'bg-gradient-to-r from-[#E11D48] to-[#7E22CE]' : 'bg-gradient-to-r from-[#F43F5E] to-[#A855F7]'">
              <span class="font-bold text-xl font-['Poppins'] text-white">VD</span>
            </div>
            <span class="text-xl font-bold font-['Poppins']" :class="isDarkMode ? 'text-white' : 'text-gray-800'">视频下载工具</span>
          </div>
          <div class="hidden md:flex items-center space-x-8">
            <a href="#" :class="isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors font-medium">首页</a>
            <a href="#platforms" :class="isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors font-medium">支持的平台</a>
            <a href="#faq" :class="isDarkMode ? 'text-gray-300 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors font-medium">常见问题</a>
            <button class="px-6 py-3 rounded-lg font-medium transition-all transform hover:scale-105 flex items-center gap-2 btn-text-white" :class="isDarkMode ? 'bg-[#E11D48] hover:bg-[#be123c]' : 'bg-[#F43F5E] hover:bg-[#e11d48]'" style="box-shadow: var(--shadow-md);">
              <CrownIcon class="w-5 h-5" />
              升级VIP
            </button>
          </div>
        </div>
      </div>
    </nav>

    <!-- 主要内容 -->
    <main class="max-w-7xl mx-auto px-6 pt-32 pb-20">
      <!-- 英雄区域 -->
      <section class="text-center mb-20 animate-fade-in">
        <h1 class="text-6xl font-bold mb-6 text-white font-['Poppins']">
          视频下载工具
        </h1>
        <p class="text-xl text-gray-300 max-w-3xl mx-auto mb-10">
          支持1800+网站的视频下载，简单易用，一键下载
        </p>
        <div class="inline-block mb-12">
          <div class="px-4 py-2 bg-[#1E1B4B] rounded-full text-sm text-gray-300 shadow-lg flex items-center gap-2">
            <FireIcon class="w-4 h-4 text-orange-500" />
            支持YouTube、B站、TikTok等1800+平台
          </div>
        </div>
        <!-- 设备展示 -->
        <div class="max-w-3xl mx-auto">
          <div class="bg-[#0F0F23] rounded-3xl p-8 shadow-2xl border border-gray-800">
            <div class="aspect-video rounded-xl overflow-hidden">
              <img :src="isDarkMode ? 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=video%20download%20tool%20interface%20modern%20dark%20theme&image_size=landscape_16_9' : 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=modern%20video%20download%20application%20light%20theme%20clean%20interface&image_size=landscape_16_9'" alt="视频下载工具界面" class="w-full h-full object-cover" />
            </div>
          </div>
        </div>
      </section>

      <!-- 下载区域 -->
      <section class="bg-[#0F0F23] rounded-2xl shadow-2xl p-10 mb-20 transform transition-all duration-300 hover:shadow-3xl border border-gray-800">
        <h2 class="text-3xl font-bold mb-10 text-center text-white font-['Poppins']">视频下载</h2>
        
        <!-- URL输入表单 -->
        <form @submit.prevent="parseVideo" class="mb-10">
          <div class="flex flex-col md:flex-row gap-4">
            <input
              v-model="videoUrl"
              type="text"
              placeholder="请输入视频URL或粘贴分享链接文本"
              class="flex-1 px-6 py-4 rounded-xl bg-gray-900 border border-gray-700 text-white focus:outline-none focus:ring-2 focus:ring-[#E11D48] transition-all"
              required
            />
            <button
              type="submit"
              :disabled="isParsing"
              class="px-8 py-4 disabled:cursor-not-allowed font-medium rounded-xl transition-all transform hover:scale-105 disabled:hover:scale-100 flex items-center gap-2 btn-text-white"
              :class="isDarkMode 
                ? 'bg-[#E11D48] hover:bg-[#be123c] disabled:bg-gray-600' 
                : 'bg-[#F43F5E] hover:bg-[#e11d48] disabled:bg-gray-400'"
              style="box-shadow: var(--shadow-md);"
            >
              <svg v-if="isParsing" class="animate-spin h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
              </svg>
              {{ isParsing ? '解析中...' : '解析视频' }}
            </button>
          </div>
          <p v-if="error" class="mt-4 text-[#E11D48] text-sm animate-fade-in">
            {{ error }}
          </p>
        </form>

        <!-- 视频信息和质量选择 -->
        <div v-if="videoInfo" class="mb-10 animate-slide-up">
          <div class="mb-8">
            <div class="flex flex-col md:flex-row gap-8">
              <div class="md:w-2/5">
                <!-- 视频封面 -->
                <div 
                  class="rounded-xl overflow-hidden shadow-lg transform transition-all duration-300 hover:scale-105 border border-gray-700 cursor-pointer relative group bg-gray-800"
                  @click="playVideo"
                >
                  <img 
                    :src="getProxyImageUrl(videoInfo.thumbnail)" 
                    :alt="videoInfo.title"
                    loading="eager"
                    decoding="async"
                    class="w-full h-auto object-cover transition-opacity duration-300 group-hover:opacity-70"
                  />
                  <div class="absolute inset-0 flex items-center justify-center bg-gradient-to-t from-black/70 to-transparent group-hover:from-black/80 transition-all duration-300">
                    <div class="transform transition-all duration-300 group-hover:scale-110">
                      <PlayIcon />
                    </div>
                  </div>
                </div>
                
                <!-- 视频标题 -->
                <h3 class="text-2xl font-bold mt-6 mb-4 text-white font-['Poppins']">{{ videoInfo.title }}</h3>
                
                <!-- 视频描述 -->
                <div v-if="videoInfo.description" class="mb-6">
                  <h4 class="font-medium mb-3 text-gray-300">视频介绍:</h4>
                  <div class="bg-gray-900/50 rounded-lg p-4 border border-gray-800">
                    <p class="text-gray-400 whitespace-pre-line">{{ videoInfo.description }}</p>
                  </div>
                </div>
                
                <!-- 视频详情信息 -->
                <div class="mt-6">
                  <h4 class="font-medium mb-3 text-gray-300">视频详情:</h4>
                  <div class="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    <p class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">时长:</span>
                      {{ formatDuration(videoInfo.duration) }}
                    </p>
                    <p class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">来源:</span>
                      {{ getVideoSource(videoUrl) }}
                    </p>
                    <p class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">格式数:</span>
                      {{ videoInfo.formats.length }}
                    </p>
                    <p v-if="videoInfo.subtitles && videoInfo.subtitles.length > 0" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">字幕:</span>
                      {{ videoInfo.subtitles.length }} 个
                    </p>
                    <p v-if="videoInfo.uploader" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">上传者:</span>
                      {{ videoInfo.uploader }}
                    </p>
                    <p v-if="videoInfo.upload_date" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">上传日期:</span>
                      {{ formatDate(videoInfo.upload_date) }}
                    </p>
                    <p v-if="videoInfo.view_count" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">观看次数:</span>
                      {{ formatNumber(videoInfo.view_count) }}
                    </p>
                    <p v-if="videoInfo.like_count" class="text-gray-400 flex items-center">
                      <span class="w-20 text-gray-500">点赞次数:</span>
                      {{ formatNumber(videoInfo.like_count) }}
                    </p>
                  </div>
                </div>
              </div>
              <div class="md:w-3/5">
                <h4 :class="isDarkMode ? 'text-gray-300' : 'text-gray-700'" class="font-medium mb-4">选择格式:</h4>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3 mb-6">
                  <div
                    v-for="format in videoInfo.formats"
                    :key="format.format_id"
                    :class="[
                      'rounded-lg p-4 cursor-pointer transition-all transform hover:scale-[1.02]',
                      isDarkMode ? 'border border-gray-700 hover:bg-gray-900' : 'border border-gray-300 hover:bg-gray-100',
                      selectedFormat === format.format_id ? 'shadow-lg ring-2' : '',
                      selectedFormat === format.format_id && isDarkMode ? 'border-[#E11D48] bg-gray-800 shadow-[#E11D48]/20 ring-[#E11D48]/30' : '',
                      selectedFormat === format.format_id && !isDarkMode ? 'border-[#F43F5E] bg-gray-100 shadow-[#F43F5E]/20 ring-[#F43F5E]/30' : ''
                    ]"
                    @click="selectedFormat = format.format_id"
                  >
                    <div class="flex justify-between items-start">
                      <div class="flex-1 min-w-0">
                        <!-- 第一行: 格式名称 + 扩展名 + 类型标签 -->
                        <div class="flex items-center gap-2 mb-2">
                          <span :class="isDarkMode ? 'text-white' : 'text-gray-800'" class="font-bold text-base truncate">
                            {{ format.resolution === '音频' ? '音频' : format.resolution }}
                          </span>
                          <span 
                            :class="isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-600'" 
                            class="px-2 py-0.5 rounded text-xs font-medium uppercase flex-shrink-0"
                          >
                            {{ format.ext }}
                          </span>
                          <span 
                            v-if="format.media_type === 'video' || format.media_type === 'audio' || format.media_type === 'merged'"
                            :class="isDarkMode ? 'bg-gray-700 text-gray-300' : 'bg-gray-200 text-gray-600'" 
                            class="px-2 py-0.5 rounded text-xs font-medium flex-shrink-0"
                          >
                            {{ format.media_type === 'video' ? '仅视频' : format.media_type === 'audio' ? '仅音频' : '音视频' }}
                          </span>
                        </div>
                        
                        <!-- 第二行: 编码信息 -->
                        <div v-if="format.format_note || format.vcodec || format.acodec" class="text-sm mb-2" :class="isDarkMode ? 'text-gray-400' : 'text-gray-500'">
                          <span v-if="format.format_note" class="font-medium">{{ format.format_note }}</span>
                          <span v-if="format.format_note && (format.vcodec || format.acodec)"> · </span>
                          <span v-if="format.vcodec">{{ format.vcodec }}</span>
                          <span v-if="format.vcodec && format.acodec"> + </span>
                          <span v-if="format.acodec">{{ format.acodec }}</span>
                        </div>
                        
                        <!-- 第三行: 文件大小 -->
                        <div v-if="format.filesize && format.filesize > 0" :class="isDarkMode ? 'text-gray-400' : 'text-gray-500'" class="text-sm">
                          <span class="font-medium">{{ formatFilesize(format.filesize) }}</span>
                        </div>
                        <div v-else :class="isDarkMode ? 'text-gray-500' : 'text-gray-400'" class="text-sm">
                          大小未知
                        </div>
                      </div>
                      
                      <div v-if="selectedFormat === format.format_id" class="ml-2 flex-shrink-0">
                        <svg class="w-6 h-6 text-[#E11D48]" fill="currentColor" viewBox="0 0 20 20">
                          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                        </svg>
                      </div>
                    </div>
                  </div>
                </div>

                <button
                  @click="downloadVideo"
                  class="w-full py-4 font-medium rounded-xl transition-all transform hover:scale-[1.02] btn-text-white"
                  :class="isDarkMode ? 'bg-[#E11D48] hover:bg-[#be123c]' : 'bg-[#F43F5E] hover:bg-[#e11d48]'"
                  :disabled="!selectedFormat"
                  style="box-shadow: var(--shadow-md);"
                >
                  下载视频
                </button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 视频播放模态框 -->
        <div v-if="isPlaying" class="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-80" @click="closeVideoPlayer">
          <div class="rounded-xl shadow-2xl p-6 max-w-4xl w-full mx-4" @click.stop>
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-xl font-bold text-white font-['Poppins']">视频播放</h3>
              <button @click="closeVideoPlayer" class="text-gray-400 hover:text-white transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
            <div class="aspect-video bg-black rounded-lg overflow-hidden">
              <video :src="videoPlayerUrl" controls autoplay controlsList="nodownload" class="w-full h-full object-contain"></video>
            </div>
          </div>
        </div>

      </section>

      <!-- 下载历史 -->
      <section class="bg-[#0F0F23] rounded-2xl shadow-2xl p-10 mb-20 transform transition-all duration-300 hover:shadow-3xl border border-gray-800">
        <div class="flex justify-between items-center mb-10">
          <h2 class="text-3xl font-bold text-white font-['Poppins']">下载历史</h2>
          <button
            @click="clearHistory"
            class="text-sm text-[#E11D48] hover:text-[#f43f5e] transition-colors transform hover:scale-105 font-medium"
          >
            清空历史
          </button>
        </div>
        <div v-if="downloadHistory.length === 0" class="text-center py-16 text-gray-400">
          <div class="flex justify-center mb-6">
            <DownloadIcon class="w-16 h-16 text-gray-600" />
          </div>
          <p class="text-lg">暂无下载历史</p>
        </div>
        <div v-else class="space-y-4">
          <div
            v-for="(item, index) in downloadHistory"
            :key="index"
            :class="isDarkMode ? 'border border-gray-700 hover:bg-gray-900/50' : 'border border-gray-300 hover:bg-gray-100'"
            class="rounded-lg p-5 transition-all duration-300 hover:shadow-md transform hover:translate-y-[-2px]"
          >
            <div class="flex justify-between items-start">
              <div>
                <h3 :class="isDarkMode ? 'text-white' : 'text-gray-800'" class="font-medium">{{ item.title }}</h3>
                <p :class="isDarkMode ? 'text-gray-400' : 'text-gray-500'" class="text-sm mt-1">{{ item.timestamp }}</p>
              </div>
              <a
                :href="item.direct_link"
                target="_blank"
                :class="isDarkMode ? 'bg-gray-800 hover:bg-gray-700 text-gray-300' : 'bg-gray-200 hover:bg-gray-300 text-gray-700'"
                class="px-4 py-2 rounded-lg transition-colors text-sm font-medium"
              >
                重新下载
              </a>
            </div>
          </div>
        </div>
      </section>

      <!-- VIP付费引导 -->
      <section class="bg-gradient-to-r from-[#1E1B4B] to-[#0F0F23] rounded-2xl shadow-2xl p-12 mb-20 transform transition-all duration-300 hover:shadow-3xl border border-gray-800">
        <div class="max-w-3xl mx-auto text-center">
          <h2 class="text-4xl font-bold mb-6 text-white font-['Poppins']">升级到VIP</h2>
          <p class="mb-8 text-lg text-gray-300">
            享受无限制下载、高速下载、批量下载等高级功能
          </p>
          <button class="px-12 py-4 font-bold rounded-xl transition-all transform hover:scale-105 mb-10 btn-text-white" :class="isDarkMode ? 'bg-[#E11D48] hover:bg-[#be123c]' : 'bg-[#F43F5E] hover:bg-[#e11d48]'" style="box-shadow: var(--shadow-md);">
            立即升级
          </button>
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            <div class="bg-gray-900/50 backdrop-blur-sm rounded-lg p-5 border border-gray-800">
              <div class="mb-4">
                <ZapIcon class="w-8 h-8 text-yellow-500" />
              </div>
              <h3 class="font-bold mb-3 text-white font-['Poppins']">高速下载</h3>
              <p class="text-sm text-gray-400">享受更快的下载速度，节省时间</p>
            </div>
            <div class="bg-gray-900/50 backdrop-blur-sm rounded-lg p-5 border border-gray-800">
              <div class="mb-4">
                <DownloadIcon class="w-8 h-8 text-blue-500" />
              </div>
              <h3 class="font-bold mb-3 text-white font-['Poppins']">批量下载</h3>
              <p class="text-sm text-gray-400">一次下载多个视频，提高效率</p>
            </div>
            <div class="bg-gray-900/50 backdrop-blur-sm rounded-lg p-5 border border-gray-800">
              <div class="mb-4">
                <ShieldIcon class="w-8 h-8 text-green-500" />
              </div>
              <h3 class="font-bold mb-3 text-white font-['Poppins']">无限制</h3>
              <p class="text-sm text-gray-400">无下载次数限制，想下多少就下多少</p>
            </div>
          </div>
        </div>
      </section>

      <!-- 支持的平台 -->
      <section id="platforms" class="mb-20">
        <h2 class="text-3xl font-bold mb-10 text-center text-white font-['Poppins']">支持的平台</h2>
        <div class="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-6">
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <YouTubeIcon class="w-12 h-12 text-[#FF0000]" />
            </div>
            <p class="font-medium text-white">YouTube</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <TikTokIcon class="w-12 h-12 text-white" />
            </div>
            <p class="font-medium text-white">TikTok</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <BilibiliIcon class="w-12 h-12 text-[#00A1D6]" />
            </div>
            <p class="font-medium text-white">B站</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <InstagramIcon class="w-12 h-12 text-[#E4405F]" />
            </div>
            <p class="font-medium text-white">Instagram</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <TwitterIcon class="w-12 h-12 text-[#1DA1F2]" />
            </div>
            <p class="font-medium text-white">Twitter</p>
          </div>
          <div class="bg-[#0F0F23] rounded-xl shadow-lg p-6 text-center transition-all duration-300 hover:shadow-xl transform hover:translate-y-[-4px] border border-gray-800">
            <div class="flex justify-center mb-4">
              <MoreIcon class="w-12 h-12 text-blue-400" />
            </div>
            <p class="font-medium text-white">1800+ 更多</p>
          </div>
        </div>
      </section>

      <!-- 常见问题 -->
      <section id="faq" class="bg-[#0F0F23] rounded-2xl shadow-2xl p-10 mb-20 border border-gray-800">
        <h2 class="text-3xl font-bold mb-10 text-center text-white font-['Poppins']">常见问题</h2>
        <div class="space-y-4">
          <div :class="isDarkMode ? 'border border-gray-700' : 'border border-gray-300'" class="rounded-lg overflow-hidden">
            <button @click="toggleFaq(0)" :class="isDarkMode ? 'hover:bg-gray-900/50 text-white' : 'hover:bg-gray-100 text-gray-800'" class="w-full px-6 py-4 text-left font-medium flex justify-between items-center transition-colors">
              <span>如何下载视频？</span>
              <ArrowDownIcon :class="['w-5 h-5 transition-transform duration-300', isDarkMode ? 'text-gray-400' : 'text-gray-500', isFaqExpanded(0) ? 'transform rotate-180' : '']" />
            </button>
            <div v-if="isFaqExpanded(0)" :class="isDarkMode ? 'bg-gray-900/30' : 'bg-gray-50'" class="px-6 py-4">
              <p :class="isDarkMode ? 'text-gray-400' : 'text-gray-600'">
                只需在输入框中粘贴视频URL，点击解析视频，选择想要的格式，然后点击下载视频按钮即可。
              </p>
            </div>
          </div>
          <div :class="isDarkMode ? 'border border-gray-700' : 'border border-gray-300'" class="rounded-lg overflow-hidden">
            <button @click="toggleFaq(1)" :class="isDarkMode ? 'hover:bg-gray-900/50 text-white' : 'hover:bg-gray-100 text-gray-800'" class="w-full px-6 py-4 text-left font-medium flex justify-between items-center transition-colors">
              <span>支持哪些网站？</span>
              <ArrowDownIcon :class="['w-5 h-5 transition-transform duration-300', isDarkMode ? 'text-gray-400' : 'text-gray-500', isFaqExpanded(1) ? 'transform rotate-180' : '']" />
            </button>
            <div v-if="isFaqExpanded(1)" :class="isDarkMode ? 'bg-gray-900/30' : 'bg-gray-50'" class="px-6 py-4">
              <p :class="isDarkMode ? 'text-gray-400' : 'text-gray-600'">
                支持YouTube、B站、TikTok、Instagram、Twitter等1800+网站的视频下载。
              </p>
            </div>
          </div>
          <div :class="isDarkMode ? 'border border-gray-700' : 'border border-gray-300'" class="rounded-lg overflow-hidden">
            <button @click="toggleFaq(2)" :class="isDarkMode ? 'hover:bg-gray-900/50 text-white' : 'hover:bg-gray-100 text-gray-800'" class="w-full px-6 py-4 text-left font-medium flex justify-between items-center transition-colors">
              <span>下载速度为什么很慢？</span>
              <ArrowDownIcon :class="['w-5 h-5 transition-transform duration-300', isDarkMode ? 'text-gray-400' : 'text-gray-500', isFaqExpanded(2) ? 'transform rotate-180' : '']" />
            </button>
            <div v-if="isFaqExpanded(2)" :class="isDarkMode ? 'bg-gray-900/30' : 'bg-gray-50'" class="px-6 py-4">
              <p :class="isDarkMode ? 'text-gray-400' : 'text-gray-600'">
                下载速度受网络环境和视频源服务器影响。升级到VIP可以获得更快的下载速度。
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <!-- 主题切换按钮 -->
    <button 
      @click="toggleDarkMode"
      class="fixed bottom-6 right-6 z-50 p-4 rounded-full bg-[#1E1B4B] hover:bg-[#2D2B55] text-white shadow-lg transition-all duration-300 transform hover:scale-110 border border-gray-700"
      title="切换主题"
    >
      <SunIcon v-if="isDarkMode" class="w-6 h-6" />
      <MoonIcon v-else class="w-6 h-6" />
    </button>

    <!-- 页脚 -->
    <footer class="bg-[#0F0F23] py-16 border-t border-gray-800">
      <div class="max-w-7xl mx-auto px-6">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-10 mb-12">
          <div>
            <h3 :class="isDarkMode ? 'text-white' : 'text-gray-800'" class="text-lg font-bold mb-6 font-['Poppins']">视频下载工具</h3>
            <p :class="isDarkMode ? 'text-gray-400' : 'text-gray-600'" class="text-sm">
              支持1800+网站的视频下载，简单易用，一键下载
            </p>
          </div>
          <div>
            <h3 :class="isDarkMode ? 'text-white' : 'text-gray-800'" class="text-lg font-bold mb-6 font-['Poppins']">快速链接</h3>
            <ul class="space-y-3 text-sm">
              <li><a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">首页</a></li>
              <li><a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">使用教程</a></li>
              <li><a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">支持的平台</a></li>
              <li><a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">关于我们</a></li>
            </ul>
          </div>
          <div>
            <h3 :class="isDarkMode ? 'text-white' : 'text-gray-800'" class="text-lg font-bold mb-6 font-['Poppins']">法律</h3>
            <ul class="space-y-3 text-sm">
              <li><a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">隐私政策</a></li>
              <li><a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">使用条款</a></li>
              <li><a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">版权声明</a></li>
            </ul>
          </div>
          <div>
            <h3 :class="isDarkMode ? 'text-white' : 'text-gray-800'" class="text-lg font-bold mb-6 font-['Poppins']">联系我们</h3>
            <ul class="space-y-3 text-sm">
              <li :class="isDarkMode ? 'text-gray-400' : 'text-gray-600'">邮箱：contact@example.com</li>
              <li :class="isDarkMode ? 'text-gray-400' : 'text-gray-600'">微信：video-download-tool</li>
            </ul>
          </div>
        </div>
        <div :class="isDarkMode ? 'border-t border-gray-800' : 'border-t border-gray-200'" class="pt-8 flex flex-col md:flex-row justify-between items-center">
          <div class="mb-4 md:mb-0">
            <p :class="isDarkMode ? 'text-gray-400' : 'text-gray-600'" class="text-sm">
              © 2026 视频下载工具. 保留所有权利.
            </p>
          </div>
          <div class="flex space-x-6">
            <a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">
              <VideoIcon class="w-6 h-6" />
            </a>
            <a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">
              <LinkIcon class="w-6 h-6" />
            </a>
            <a href="#" :class="isDarkMode ? 'text-gray-400 hover:text-white' : 'text-gray-600 hover:text-gray-900'" class="transition-colors">
              <DownloadIcon class="w-6 h-6" />
            </a>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import axios from 'axios';
import { FireIcon, VideoIcon, DownloadIcon, LinkIcon, CrownIcon, ShieldIcon, ZapIcon, HeartIcon, ArrowDownIcon, MoreIcon, PlayIcon, BilibiliIcon, YouTubeIcon, TikTokIcon, InstagramIcon, TwitterIcon, SunIcon, MoonIcon } from './icons'

export default {
  name: 'App',
  components: {
    FireIcon,
    VideoIcon,
    DownloadIcon,
    LinkIcon,
    CrownIcon,
    ShieldIcon,
    ZapIcon,
    HeartIcon,
    ArrowDownIcon,
    MoreIcon,
    PlayIcon,
    BilibiliIcon,
    YouTubeIcon,
    TikTokIcon,
    InstagramIcon,
    TwitterIcon,
    SunIcon,
    MoonIcon
  },
  data() {
    return {
      videoUrl: '',
      videoInfo: null,
      selectedFormat: '',
      error: '',
      downloadHistory: JSON.parse(localStorage.getItem('downloadHistory') || '[]'),
      isPlaying: false,
      videoPlayerUrl: '',
      isParsing: false,
      expandedFaqs: [0], // 默认展开第一个问题
      isDarkMode: true, // 默认暗色模式
      parseSource: 'auto' // B站解析源: auto, injahow, ytdlp, both
    };
  },
  computed: {
    isBilibiliUrl() {
      const url = this.videoUrl.toLowerCase();
      return url.includes('bilibili.com') || url.includes('b23.tv');
    }
  },
  methods: {
    extractUrlFromText(text) {
      // 从文本中提取URL
      const urlRegex = /(https?:\/\/[^\s]+)/g;
      const matches = text.match(urlRegex);
      return matches ? matches[0] : text;
    },
    async parseVideo() {
      try {
        this.isParsing = true;
        this.error = '';
        this.videoInfo = null;
        this.selectedFormat = '';
        
        // 从输入文本中提取URL
        const extractedUrl = this.extractUrlFromText(this.videoUrl);
        
        const response = await axios.get('http://localhost:8000/api/parse', {
          params: { url: extractedUrl }
        });
        
        this.videoInfo = response.data;
      } catch (error) {
        this.error = error.response?.data?.detail || '解析失败，请检查URL是否正确';
      } finally {
        this.isParsing = false;
      }
    },
    async downloadVideo() {
      if (!this.selectedFormat) return;
      
      try {
        this.error = '';
        
        // 从输入文本中提取URL
        const extractedUrl = this.extractUrlFromText(this.videoUrl);
        
        const response = await axios.get('http://localhost:8000/api/download', {
          params: {
            url: extractedUrl,
            format_id: this.selectedFormat
          }
        });
        
        // 保存到下载历史
        this.saveToHistory(response.data);
        
        // 使用后端代理下载，避免跨域和403问题
        const downloadUrl = `http://localhost:8000/api/proxy-download?url=${encodeURIComponent(response.data.direct_link)}&filename=${encodeURIComponent(response.data.title)}.${response.data.ext}`;
        window.open(downloadUrl, '_blank');
      } catch (error) {
        this.error = error.response?.data?.detail || '下载失败，请稍后重试';
      }
    },
    saveToHistory(videoData) {
      const historyItem = {
        title: videoData.title,
        direct_link: videoData.direct_link,
        timestamp: new Date().toLocaleString()
      };
      
      this.downloadHistory.unshift(historyItem);
      // 只保留最近10条记录
      if (this.downloadHistory.length > 10) {
        this.downloadHistory = this.downloadHistory.slice(0, 10);
      }
      
      localStorage.setItem('downloadHistory', JSON.stringify(this.downloadHistory));
    },
    clearHistory() {
      this.downloadHistory = [];
      localStorage.removeItem('downloadHistory');
    },
    formatDuration(seconds) {
      if (!seconds) return '未知';
      const hours = Math.floor(seconds / 3600);
      const minutes = Math.floor((seconds % 3600) / 60);
      const secs = Math.floor(seconds % 60);
      
      if (hours > 0) {
        return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
      } else {
        return `${minutes}:${secs.toString().padStart(2, '0')}`;
      }
    },
    formatFilesize(bytes) {
      if (!bytes) return '未知';
      const units = ['B', 'KB', 'MB', 'GB'];
      let size = bytes;
      let unitIndex = 0;
      
      while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
      }
      
      return `${size.toFixed(2)} ${units[unitIndex]}`;
    },
    getProxyImageUrl(url) {
      if (!url) return '';
      // 使用后端代理接口处理跨域图片
      return `http://localhost:8000/api/proxy-image?url=${encodeURIComponent(url)}`;
    },
    getVideoSource(url) {
      if (!url) return '未知';
      
      const platforms = {
        'youtube.com': 'YouTube',
        'bilibili.com': 'B站',
        'douyin.com': '抖音',
        'tiktok.com': 'TikTok',
        'instagram.com': 'Instagram',
        'twitter.com': 'Twitter',
        'facebook.com': 'Facebook',
        'reddit.com': 'Reddit',
        'vimeo.com': 'Vimeo',
        'dailymotion.com': 'Dailymotion'
      };
      
      for (const [domain, name] of Object.entries(platforms)) {
        if (url.includes(domain)) {
          return name;
        }
      }
      
      return '其他平台';
    },
    formatDate(dateStr) {
      if (!dateStr) return '未知';
      // 处理YYYYMMDD格式的日期
      if (dateStr.length === 8) {
        const year = dateStr.substring(0, 4);
        const month = dateStr.substring(4, 6);
        const day = dateStr.substring(6, 8);
        return `${year}-${month}-${day}`;
      }
      return dateStr;
    },
    formatNumber(num) {
      if (!num) return '未知';
      // 格式化数字，添加千位分隔符
      return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },
    async playVideo() {
      // 播放视频
      if (this.videoInfo && this.videoInfo.formats && this.videoInfo.formats.length > 0) {
        try {
          // 选择最高清晰度的格式
          const highestFormat = this.videoInfo.formats[this.videoInfo.formats.length - 1];
          
          // 如果有预加载的代理地址，直接使用
          if (this.videoInfo.proxy_urls && this.videoInfo.proxy_urls[highestFormat.format_id]) {
            this.videoPlayerUrl = this.videoInfo.proxy_urls[highestFormat.format_id];
            this.isPlaying = true;
            return;
          }
          
          // B站视频使用 injahow 播放源
          if (this.isBilibiliUrl) {
            const extractedUrl = this.extractUrlFromText(this.videoUrl);
            const response = await axios.get('http://localhost:8000/api/get-direct-link', {
              params: {
                url: extractedUrl,
                format_id: highestFormat.format_id,
                source: 'injahow'
              }
            });
            this.videoPlayerUrl = response.data.direct_link;
            this.isPlaying = true;
            return;
          }
          
          // 其他平台需要请求获取代理地址
          const extractedUrl = this.extractUrlFromText(this.videoUrl);
          const response = await axios.get('http://localhost:8000/api/get-direct-link', {
            params: {
              url: extractedUrl,
              format_id: highestFormat.format_id
            }
          });
          this.videoPlayerUrl = response.data.direct_link;
          this.isPlaying = true;
        } catch (error) {
          this.error = '视频播放失败，请稍后重试';
        }
      }
    },
    closeVideoPlayer() {
      this.isPlaying = false;
      this.videoPlayerUrl = '';
    },
    toggleFaq(index) {
      const i = this.expandedFaqs.indexOf(index);
      if (i > -1) {
        this.expandedFaqs.splice(i, 1);
      } else {
        this.expandedFaqs.push(index);
      }
    },
    isFaqExpanded(index) {
      return this.expandedFaqs.includes(index);
    },
    toggleDarkMode() {
      this.isDarkMode = !this.isDarkMode;
      document.documentElement.classList.toggle('dark', this.isDarkMode);
      localStorage.setItem('darkMode', this.isDarkMode);
    }
  },
  mounted() {
    // 从localStorage恢复主题设置
    const savedMode = localStorage.getItem('darkMode');
    if (savedMode !== null) {
      this.isDarkMode = savedMode === 'true';
      document.documentElement.classList.toggle('dark', this.isDarkMode);
    }
  }
};
</script>

<style scoped>
/* 组件样式 */
.animate-fade-in {
  animation: fadeIn 0.6s ease-in-out;
}

.animate-slide-up {
  animation: slideUp 0.6s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideUp {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}
</style>

<style>
/* 全局样式 */
:root {
  --bg-primary: #0F0F23;
  --bg-secondary: #1E1B4B;
  --bg-tertiary: #1a1a3a;
  --text-primary: #ffffff;
  --text-secondary: #e5e5e5;
  --text-muted: #a3a3a3;
  --border-color: #33334d;
  --accent-color: #E11D48;
  --accent-hover: #be123c;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.3);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.4), 0 2px 4px -2px rgb(0 0 0 / 0.4);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.5), 0 4px 6px -4px rgb(0 0 0 / 0.5);
}

/* 亮模式 */
:root:not(.dark) {
  --bg-primary: #ffffff;
  --bg-secondary: #f8fafc;
  --bg-tertiary: #f1f5f9;
  --text-primary: #1e293b;
  --text-secondary: #334155;
  --text-muted: #64748b;
  --border-color: #e2e8f0;
  --accent-color: #F43F5E;
  --accent-hover: #e11d48;
  --shadow-sm: 0 1px 2px 0 rgb(0 0 0 / 0.05);
  --shadow-md: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
  --shadow-lg: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1);
}

/* 应用主题变量 */
body {
  background-color: var(--bg-primary);
  color: var(--text-primary);
  transition: all 0.3s ease;
}

/* 覆盖默认样式 */
.bg-\[\#0F0F23\],
.bg-gray-900,
.bg-gray-800 {
  background-color: var(--bg-primary) !important;
}

.bg-\[\#1E1B4B\],
.bg-gray-900\/50 {
  background-color: var(--bg-secondary) !important;
}

.bg-gray-900\/30 {
  background-color: var(--bg-tertiary) !important;
}

.text-white {
  color: var(--text-primary) !important;
}

/* 按钮文字颜色 - 始终为白色 */
.btn-text-white {
  color: white !important;
}

.text-gray-400,
.text-gray-500,
.text-gray-600 {
  color: var(--text-muted) !important;
}

.border-gray-800,
.border-gray-700 {
  border-color: var(--border-color) !important;
}

/* 移除可能导致冲突的覆盖规则，让按钮颜色能正确响应:class绑定 */

.text-gray-300 {
  color: var(--text-secondary) !important;
}

.hover\:text-white:hover {
  color: var(--text-primary) !important;
}

/* 按钮文字悬浮时保持白色 */
.btn-text-white:hover {
  color: white !important;
}

/* 主题切换按钮 */
.fixed.bottom-6.right-6 {
  background-color: var(--bg-secondary) !important;
  border-color: var(--border-color) !important;
  color: var(--text-primary) !important;
}

.fixed.bottom-6.right-6:hover {
  background-color: var(--bg-tertiary) !important;
}

/* 模态框 */
.fixed.inset-0 {
  background-color: rgba(0, 0, 0, 0.8) !important;
}

.fixed.inset-0 > div {
  background-color: var(--bg-primary) !important;
  border-color: var(--border-color) !important;
}

/* 渐变背景 */
.bg-gradient-to-r {
  background: linear-gradient(to right, var(--bg-secondary), var(--bg-primary)) !important;
}

/* 页脚样式 */
footer {
  background-color: var(--bg-primary) !important;
  border-top-color: var(--border-color) !important;
}

footer h3 {
  color: var(--text-primary) !important;
}

footer p {
  color: var(--text-muted) !important;
}

footer a {
  color: var(--text-muted) !important;
}

footer a:hover {
  color: var(--text-primary) !important;
}
</style>
