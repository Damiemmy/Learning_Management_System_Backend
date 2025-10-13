from django.db import models
from userauth.models import Profile,User
from django.utils.text import slugify
from shortuuid.django_fields import ShortUUIDField
from django.utils import timezone
from moviepy.editor import VideoFileClip
import math
# Create your models here.
LANGUAGE=(
    ("English","English"),
    ("Spanish","Spanish"),
    ("French","French"),

)
LEVEL=(
    ("Beginner","Beginner"),
    ("Intermidiate","Intermidiate"),
    ("Advanced","Advanced"),

)
TEACHER_STATUS=(
    ("Draft","Draft"),
    ("Disabled","Disabled"),
    ("Published","Published"),

)
PLATFORM_STATUS=(
    ("Review","Review"),
    ("Disabled","Disabled"),
    ("Rejected","Rejected"),
    ("Draft","Draft"),
    ("Published","Published"),

)


class Teacher(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    image=models.FileField(upload_to='course-file',blank=True,null=True,default='default.jpg')
    full_name=models.CharField(max_length=100)
    bio=models.CharField(max_length=100,null=True,blank=True)
    facebook=models.URLField(null=True,blank=True)
    twitter=models.URLField(null=True,blank=True)
    linkedin=models.URLField(null=True,blank=True)
    about=models.TextField(null=True,blank=True)
    country=models.CharField(max_length=100,null=True,blank=True)

    def __str__(self):
        return self.full_name
    
    def students(self):
        return CartOrderItem.objects.filter(teacher=self)
    def courses(self):
        return Course.objects.filter(teacher=self)
    def review(self):
        return Course.objects.filter(teacher=self).count()

class Category(models.Model):
    title = models.CharField(max_length=100)
    image = models.FileField(upload_to='course-file',default='category.jpg',null=True,blank=True)
    slug = models.SlugField(unique=True,null=True,blank=True)

    class Meta:
        verbose_name_plural="Category"
        ordering=['title']

    def __str__(self):
        return self.title

    def course_count(self):
        return Course.objects.filter(category=self).count()

    def save(self,*args,**kwargs):
        if self.slug == "" or self.slug == None:
            self.slug=slugify(self.title)

        super(Category,self).save(*args,**kwargs)

class Course(models.Model):
    category=models.ForeignKey(Category,on_delete=models.SET_NULL,null=True,blank=True)
    teacher=models.ForeignKey(Teacher,on_delete=models.CASCADE)
    file=models.FileField(upload_to='course-file',blank=True,null=True)
    image=models.FileField(upload_to="course-file",blank=True,null=True)
    title=models.CharField(max_length=200)
    description=models.TextField(null=True,blank=True)
    price=models.DecimalField(max_digits=12,decimal_places=2,default=0.00)
    language=models.CharField(max_length=15,choices=LANGUAGE, default='English')
    level=models.CharField(choices=LEVEL, default="Beginner", max_length=15)
    platform_status=models.CharField(max_length=15, choices=PLATFORM_STATUS, default="Published ")
    teacher_course_status=models.CharField(max_length=15, choices=TEACHER_STATUS, default="Published")
    featured=models.BooleanField(default=False)
    course_id=ShortUUIDField(unique=True,length=6,max_length=20,alphabet="1234567890")
    slug=models.SlugField(unique=True)
    date=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    def save(self,*args,**kwargs):
        if self.slug == "" or self.slug == None:
            self.slug=slugify(self.title)

        super(Course,self).save(*args,**kwargs)
    
    def students(self):
        return EnrolledCourse.objects.filter(course=self)

    def curriculum(self):
        return VariantItem.objects.filter(variant__course=self)

    def lectures(self):
        return VariantItem.objects.filter(variant__course=self)

    def average_rating(self):
        average_rating = Review.objects.filter(course=self).aggregate(avg_rating=models.Avg('rating'))
        return average_rating['avg_rating']
    
    def rating_count(self):
        return Review.objects.filter(course=self).count()

    def reviews(self):
        return Review.objects.filter(course=self,active=True)

class Variant(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    title=models.CharField(max_length=1000)
    variant_id=ShortUUIDField(unique=True,length=6,max_length=20,alphabet='123456789')
    date=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    def variant_items(self):
        return VariantItem.objects.filter(variant=self)

class VariantItem(models.Model):
    variant=models.ForeignKey(Variant,on_delete=models.CASCADE,related_name="variant_items")
    title= models.CharField(max_length=1000)
    file=models.FileField(upload_to="course-file")
    duration=models.DurationField(null=True,blank=True)
    content_duration=models.CharField(max_length=1000,null=True,blank=True)
    preview=models.BooleanField(default=False)
    variant_item_id= ShortUUIDField(unique=True,length=6,max_length=20,alphabet="123456789")
    date=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.variant.title} - {self.title}"

    def save(self,*args,**kwargs):
        super().save(*args,**kwargs)

        if self.file:
            clip = VideoFileClip(self.file.path)
            duration_seconds=clip.duration

            minutes,remainder=divmod(duration_seconds,60)
            minutes=math.floor(minutes)
            seconds=math.floor(remainder)

            duration_text=f"{minutes}m {seconds}s"
            self.content_duration=duration_text
            super().save(update_fields=['content_duration'])

class Question_Answer(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    title=models.CharField(max_length=1000,null=True,blank=True)
    date=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}- {self.course.title}"

    class Meta:
        ordering =['-date']
    
    def messages(self):
        return Question_Answer_Message.objects.filter(question=self)

    def profile(self):
        return Profile.objects.get(user=self.user)

class Question_Answer_Message(models.Model):
    course=models.ForeignKey(Course,on_delete=models.CASCADE)
    question=models.ForeignKey(Question_Answer,on_delete=models.CASCADE)
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    message=models.TextField(null=True,blank=True)
    qam_id=ShortUUIDField(unique=True,length=6,max_length=20,alphabet="123456789")
    date=models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user.username}-{self.course.title}"
    
    class Meta:
        ordering=['date']



