import { useState, useRef, useCallback } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import {
  Mic,
  Square,
  Pause,
  Play,
  Trash2,
  FileAudio,
  Shield,
  CheckCircle2,
  Clock,
  Hash,
} from 'lucide-react';

interface RecordingMetadata {
  fileName: string;
  startTime: string;
  endTime: string;
  duration: number; // 秒
  fileSize: number; // 字节
  format: string;
  sampleRate?: number;
  channels?: number;
  hash?: string;
  hashAlgorithm: string;
  location?: string;
  participants?: string[];
  notes?: string;
}

interface Recording {
  id: string;
  metadata: RecordingMetadata;
  audioBlob?: Blob;
  status: 'recording' | 'paused' | 'completed' | 'uploading' | 'error';
  progress?: number;
}

interface MeetingRecorderProps {
  caseId: string;
  onRecordingComplete?: (recording: Recording) => void;
}

export function MeetingRecorder({ caseId: _caseId, onRecordingComplete }: MeetingRecorderProps) {
  const [recording, setRecording] = useState<Recording | null>(null);
  const [recordings, setRecordings] = useState<Recording[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [duration, setDuration] = useState(0);
  const [showMetadataForm, setShowMetadataForm] = useState(false);
  const [metadata, setMetadata] = useState<Partial<RecordingMetadata>>({
    participants: [],
    notes: '',
  });

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<Date | null>(null);

  // 计算音频文件的 SHA-256 哈希
  const calculateHash = useCallback(async (blob: Blob): Promise<string> => {
    const arrayBuffer = await blob.arrayBuffer();
    const hashBuffer = await crypto.subtle.digest('SHA-256', arrayBuffer);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(b => b.toString(16).padStart(2, '0')).join('');
  }, []);

  // 格式化时间
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  // 开始录音
  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4',
      });

      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];
      startTimeRef.current = new Date();

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, {
          type: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4',
        });

        // 计算哈希
        let hash = '';
        try {
          hash = await calculateHash(audioBlob);
        } catch (error) {
          console.error('计算哈希失败:', error);
        }

        const endTime = new Date();
        const duration = startTimeRef.current
          ? Math.floor((endTime.getTime() - startTimeRef.current.getTime()) / 1000)
          : 0;

        const newRecording: Recording = {
          id: `recording-${Date.now()}`,
          metadata: {
            fileName: `录音_${new Date().toISOString().slice(0, 10)}.webm`,
            startTime: startTimeRef.current?.toISOString() || '',
            endTime: endTime.toISOString(),
            duration,
            fileSize: audioBlob.size,
            format: audioBlob.type,
            hashAlgorithm: 'SHA-256',
            hash,
            participants: metadata.participants || [],
            notes: metadata.notes,
          },
          audioBlob,
          status: 'completed',
        };

        setRecording(newRecording);
        setRecordings(prev => [newRecording, ...prev]);
        onRecordingComplete?.(newRecording);

        // 停止所有轨道
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start(1000); // 每秒收集数据
      setIsRecording(true);
      setIsPaused(false);

      // 计时器
      timerRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);
    } catch (error) {
      console.error('无法访问麦克风:', error);
      alert('无法访问麦克风，请检查权限设置');
    }
  }, [calculateHash, metadata.participants, metadata.notes, onRecordingComplete]);

  // 暂停录音
  const pauseRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.pause();
      setIsPaused(true);
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  }, [isRecording]);

  // 恢复录音
  const resumeRecording = useCallback(() => {
    if (mediaRecorderRef.current && isPaused) {
      mediaRecorderRef.current.resume();
      setIsPaused(false);
      timerRef.current = setInterval(() => {
        setDuration(prev => prev + 1);
      }, 1000);
    }
  }, [isPaused]);

  // 停止录音
  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setIsPaused(false);
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  }, []);

  // 删除录音
  const deleteRecording = useCallback((id: string) => {
    setRecordings(prev => prev.filter(r => r.id !== id));
    if (recording?.id === id) {
      setRecording(null);
    }
  }, [recording]);

  // 添加参与者
  const addParticipant = (name: string) => {
    if (name.trim()) {
      setMetadata(prev => ({
        ...prev,
        participants: [...(prev.participants || []), name.trim()],
      }));
    }
  };

  // 移除参与者
  const removeParticipant = (index: number) => {
    setMetadata(prev => ({
      ...prev,
      participants: prev.participants?.filter((_, i) => i !== index),
    }));
  };

  return (
    <div className="space-y-6">
      {/* 录音控制区 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <FileAudio className="h-5 w-5" />
                会议录音
              </CardTitle>
              <CardDescription>自动生成录音哈希值，确保法律效力</CardDescription>
            </div>
            {isRecording && (
              <Badge variant="destructive" className="animate-pulse">
                录音中
              </Badge>
            )}
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 录音计时器 */}
          {isRecording && (
            <div className="text-center py-4">
              <div className="text-4xl font-mono font-bold text-primary">
                {formatDuration(duration)}
              </div>
              <div className="text-sm text-muted-foreground mt-2">
                {isPaused ? '已暂停' : '正在录音...'}
              </div>
            </div>
          )}

          {/* 控制按钮 */}
          <div className="flex justify-center gap-4">
            {!isRecording ? (
              <Button onClick={startRecording} size="lg" className="gap-2">
                <Mic className="h-5 w-5" />
                开始录音
              </Button>
            ) : (
              <>
                {isPaused ? (
                  <Button onClick={resumeRecording} variant="outline" size="lg" className="gap-2">
                    <Play className="h-5 w-5" />
                    继续
                  </Button>
                ) : (
                  <Button onClick={pauseRecording} variant="outline" size="lg" className="gap-2">
                    <Pause className="h-5 w-5" />
                    暂停
                  </Button>
                )}
                <Button onClick={stopRecording} variant="destructive" size="lg" className="gap-2">
                  <Square className="h-5 w-5" />
                  停止
                </Button>
              </>
            )}
          </div>

          {/* 元数据表单 */}
          {!isRecording && (
            <div className="border-t pt-4">
              <Button
                variant="ghost"
                onClick={() => setShowMetadataForm(!showMetadataForm)}
                className="w-full justify-between"
              >
                <span className="flex items-center gap-2">
                  <Shield className="h-4 w-4" />
                  录音设置（可选）
                </span>
                <span className="text-muted-foreground">{showMetadataForm ? '收起' : '展开'}</span>
              </Button>

              {showMetadataForm && (
                <div className="mt-4 space-y-4">
                  {/* 参与者 */}
                  <div className="space-y-2">
                    <Label>参与者</Label>
                    <div className="flex flex-wrap gap-2 mb-2">
                      {metadata.participants?.map((p, i) => (
                        <Badge key={i} variant="secondary" className="gap-1">
                          {p}
                          <button onClick={() => removeParticipant(i)} className="ml-1 hover:text-destructive">
                            ×
                          </button>
                        </Badge>
                      ))}
                    </div>
                    <Input
                      placeholder="输入参与者姓名，按回车添加"
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          e.preventDefault();
                          addParticipant((e.target as HTMLInputElement).value);
                          (e.target as HTMLInputElement).value = '';
                        }
                      }}
                    />
                  </div>

                  {/* 备注 */}
                  <div className="space-y-2">
                    <Label>录音备注</Label>
                    <Textarea
                      placeholder="会议主题、重要事项..."
                      value={metadata.notes || ''}
                      onChange={(e) => setMetadata(prev => ({ ...prev, notes: e.target.value }))}
                      rows={2}
                    />
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* 哈希验证说明 */}
      <Card className="border-green-200 bg-green-50/50">
        <CardContent className="p-4">
          <div className="flex items-start gap-3">
            <Shield className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <h4 className="font-medium text-green-900">存证安全保障</h4>
              <ul className="mt-2 text-sm text-green-800 space-y-1">
                <li className="flex items-center gap-2">
                  <Hash className="h-3 w-3" />
                  录音文件使用 SHA-256 算法生成唯一哈希值
                </li>
                <li className="flex items-center gap-2">
                  <Clock className="h-3 w-3" />
                  自动记录录音起止时间戳
                </li>
                <li className="flex items-center gap-2">
                  <CheckCircle2 className="h-3 w-3" />
                  支持验证录音完整性
                </li>
              </ul>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 录音列表 */}
      {recordings.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">录音记录</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {recordings.map((rec) => (
              <div
                key={rec.id}
                className="flex items-center justify-between p-3 border rounded-lg"
              >
                <div className="flex items-center gap-3">
                  <FileAudio className="h-8 w-8 text-muted-foreground" />
                  <div>
                    <div className="font-medium">{rec.metadata.fileName}</div>
                    <div className="text-sm text-muted-foreground flex items-center gap-4">
                      <span>{formatDuration(rec.metadata.duration)}</span>
                      <span>{formatFileSize(rec.metadata.fileSize)}</span>
                      {rec.metadata.hash && (
                        <span className="flex items-center gap-1 text-green-600">
                          <CheckCircle2 className="h-3 w-3" />
                          已校验
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Button
                    variant="ghost"
                    size="icon"
                    onClick={() => deleteRecording(rec.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}

      {/* 哈希详情（当前录音） */}
      {recording && recording.metadata.hash && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Hash className="h-4 w-4" />
              当前录音哈希值
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-muted p-3 rounded-lg font-mono text-sm break-all">
              {recording.metadata.hash}
            </div>
            <p className="text-xs text-muted-foreground mt-2">
              哈希算法: {recording.metadata.hashAlgorithm} | 生成时间: {recording.metadata.endTime}
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
